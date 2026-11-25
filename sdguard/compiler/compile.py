"""``sdguard compile``: instruction files in, a validated rule package out.

Pipeline (docs/plan/01_MIMARI.md §2.1):

1. **Extract** (code): list items and paragraphs, with line numbers; a keyword filter.
2. **Classify** (LLM, one call per file): atomic rules, category, CWE.
3. **Translate** (LLM, one call per non-vague rule): deny entries, a Semgrep rule with its
   test file, or a pytest file with reference applications.
4. **Validate** (code): permission examples, ``semgrep --test``, pytest against the
   reference applications in a network-less runner.
5. **Repair**: a failed validation goes back to the model with the validator's message, at
   most ``max_attempts`` times in all. A rule that still fails is kept as advice.
6. **Write** the package (``.sdguard/``):

   rules.ir.json           the RuleSet (contract: sdguard/contracts/rules.py)
   semgrep/R-xxx.yaml      Semgrep rules, with semgrep/tests/R-xxx.py
   tests/security/*.py     behavior tests
   examples/R-xxx/         reference applications of each behavior test
   rejected/R-xxx/         the last failed attempt of rules that became advice
   advisory.md             rules that are only advice, for the agent's context
   report.md               what was compiled, verified, rejected and why
   compile-log.jsonl       every model call: prompt, answer, validation, cost

The rules' enforcement follows one fixed policy (``ENFORCEMENT``), not the model.
"""

import hashlib
import json
import os
import shutil
import tempfile
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from sdguard.compiler import prompts
from sdguard.compiler.behavior_runner import BehaviorRunner
from sdguard.compiler.extract import Candidate, extract_candidates
from sdguard.compiler.llm import Llm, LlmError, LlmUnavailable
from sdguard.compiler.neutral_apps import NEUTRAL_APPS
from sdguard.compiler.permission_validation import validate_permissions
from sdguard.compiler.schemas import (
    ActionTranslation,
    BehaviorTranslation,
    Classification,
    ClassifiedRule,
    CodeTranslation,
)
from sdguard.compiler.semgrep_validation import rule_ids, validate_semgrep
from sdguard.contracts.rules import (
    AgentName,
    CompiledBy,
    Coverage,
    Enforcement,
    PermissionTarget,
    PytestTarget,
    Rule,
    RuleCategory,
    RuleSet,
    SemgrepTarget,
    SourceFile,
    SourceRef,
    Targets,
    Validation,
    ValidationStatus,
)

ENFORCEMENT: dict[RuleCategory, Enforcement] = {
    RuleCategory.ACTION: Enforcement.BLOCK,  # deny the tool call
    RuleCategory.CODE: Enforcement.BLOCK,  # do not let the turn end with the finding
    RuleCategory.BEHAVIOR: Enforcement.BLOCK,  # do not let the turn end with a failing test
}
DEFAULT_MAX_ATTEMPTS = 3  # the first answer and two repairs

# Gaps the compiler knows from the spikes; added whatever the model claims.
READ_DENY_GAP = (
    "A folder-wide search such as 'grep -r KEY .' returns the file's content without "
    "naming the file; the Read deny entry does not stop it (spike 05)."
)
AGY_FILE_GAP = (
    "Antigravity: only the listed paths are covered; a file with the same name in another "
    "folder or created later is not (no wildcards in file targets, spike 06C)."
)

MANAGED = (
    "rules.ir.json",
    "advisory.md",
    "report.md",
    "compile-log.jsonl",
    "semgrep",
    "tests",
    "examples",
    "rejected",
)


class CompileError(RuntimeError):
    """Compilation cannot go on (bad input, or the model is unavailable)."""


@dataclass
class RuleOutcome:
    rule: Rule
    restated: str  # the classifier's atomic restatement, shown in the report
    files: dict[str, str] = field(default_factory=dict)  # package path -> content
    rejected_files: dict[str, str] = field(default_factory=dict)


@dataclass
class CompileResult:
    ruleset: RuleSet
    outcomes: list[RuleOutcome]
    dropped: list[tuple[str, Candidate]]  # (file, candidate) left out by the keyword filter
    not_security: list[tuple[str, Candidate]]  # judged not security related by the model
    log: list[dict[str, Any]]
    left_out: list[tuple[str, Candidate]] = field(default_factory=list)  # model skipped them

    @property
    def files(self) -> dict[str, str]:
        out: dict[str, str] = {}
        for outcome in self.outcomes:
            out.update(outcome.files)
            out.update(outcome.rejected_files)
        out["rules.ir.json"] = self.ruleset.model_dump_json(indent=2, exclude_none=True) + "\n"
        out["advisory.md"] = render_advisory(self.ruleset)
        out["report.md"] = render_report(self)
        out["compile-log.jsonl"] = "".join(
            json.dumps(entry, ensure_ascii=False) + "\n" for entry in self.log
        )
        return out


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class _Built:
    validation: Validation
    targets: Targets
    coverage: Coverage
    known_gaps: list[str]
    files: dict[str, str]


class _Session:
    """One compilation: the model, the runner, the log."""

    def __init__(
        self,
        llm: Llm,
        runner: BehaviorRunner,
        work: Path,
        max_attempts: int,
        progress: Callable[[str], None],
    ) -> None:
        self.llm = llm
        self.runner = runner
        self.work = work
        self.max_attempts = max_attempts
        self.progress = progress
        self.log: list[dict[str, Any]] = []

    def ask(
        self,
        stage: str,
        rule_id: str | None,
        attempt: int,
        system: str,
        prompt: str,
        schema: type[BaseModel],
    ) -> dict[str, Any] | None:
        entry: dict[str, Any] = {
            "stage": stage,
            "rule_id": rule_id,
            "attempt": attempt,
            "model": self.llm.model,
            "system_sha256": _sha256(system),
            "prompt": prompt,
        }
        started = time.monotonic()
        try:
            reply = self.llm.ask(system, prompt, schema)
        except LlmUnavailable as exc:
            entry |= {"error": str(exc), "duration_s": round(time.monotonic() - started, 2)}
            self.log.append(entry)
            raise CompileError(str(exc)) from exc
        except LlmError as exc:
            entry |= {"error": str(exc), "duration_s": round(time.monotonic() - started, 2)}
            self.log.append(entry)
            return None
        entry |= {"answer": reply.data, "duration_s": reply.duration_s, "cost_usd": reply.cost_usd}
        self.log.append(entry)
        return reply.data

    # --- classification -------------------------------------------------------------------

    def classify(
        self, file: str, candidates: list[Candidate]
    ) -> tuple[list[ClassifiedRule], set[int], set[int]]:
        """Return (rules, lines judged not security, lines the model left out)."""
        if not candidates:
            return [], set(), set()
        self.progress(f"classify {file}: {len(candidates)} candidate statements")
        known = {c.line for c in candidates}
        base = prompts.classify_prompt(candidates)
        prompt = base
        result: Classification | None = None
        for attempt in range(1, self.max_attempts + 1):
            data = self.ask(
                "classify", None, attempt, prompts.CLASSIFY_SYSTEM, prompt, Classification
            )
            if data is None:
                continue
            answer = Classification.model_validate(data)
            unknown = sorted({r.source_line for r in answer.rules} - known)
            if unknown:
                problem = f"source_line values {unknown} are not candidate lines"
                self.log[-1]["validation"] = problem
                prompt = prompts.repair_prompt(base, data, problem)
                continue
            result = answer
            missing = sorted(
                known - {r.source_line for r in answer.rules} - set(answer.not_security)
            )
            if not missing:
                break
            problem = f"candidate lines {missing} are neither in a rule nor in not_security"
            self.log[-1]["validation"] = problem
            prompt = prompts.repair_prompt(base, data, problem)
        if result is None:
            raise CompileError(f"{file}: classification failed {self.max_attempts} times")
        covered = {r.source_line for r in result.rules}
        not_security = set(result.not_security) & known - covered
        left_out = known - covered - not_security
        return sorted(result.rules, key=lambda r: r.source_line), not_security, left_out

    # --- translation ------------------------------------------------------------------------

    def translate(self, rule_id: str, classified: ClassifiedRule, source: SourceRef) -> RuleOutcome:
        category = classified.category
        if category is RuleCategory.VAGUE:
            return RuleOutcome(_advice(rule_id, classified, source, None), classified.text)
        system: str
        schema: type[BaseModel]
        check: Callable[[str, BaseModel, int], _Built]
        if category is RuleCategory.ACTION:
            system, schema, check = prompts.ACTION_SYSTEM, ActionTranslation, self._check_action
        elif category is RuleCategory.CODE:
            system, schema, check = prompts.CODE_SYSTEM, CodeTranslation, self._check_code
        else:
            system, schema = prompts.BEHAVIOR_SYSTEM, BehaviorTranslation
            check = self._check_behavior
        base = prompts.translate_prompt(
            rule_id, classified.text, source.text, source.file, source.line, classified.cwe
        )
        prompt = base
        last_validation: Validation | None = None
        last_files: dict[str, str] = {}
        for attempt in range(1, self.max_attempts + 1):
            self.progress(f"{rule_id} ({category.value}) attempt {attempt}")
            data = self.ask("translate", rule_id, attempt, system, prompt, schema)
            if data is None:
                last_validation = Validation(
                    status=ValidationStatus.FAILED, attempts=attempt,
                    message=f"attempt {attempt}: the model gave no valid answer",
                )  # fmt: skip
                continue
            answer = schema.model_validate(data)
            built = check(rule_id, answer, attempt)
            self.log[-1]["validation"] = built.validation.model_dump(mode="json")
            if built.validation.status is ValidationStatus.VERIFIED:
                try:
                    rule = Rule(
                        id=rule_id,
                        source=source,
                        category=category,
                        cwe=classified.cwe,
                        targets=built.targets,
                        validation=built.validation,
                        enforcement=ENFORCEMENT[category],
                        coverage=built.coverage,
                        known_gaps=built.known_gaps,
                    )
                except ValueError as exc:  # the rule format contract refuses the result
                    built = replace(
                        built, validation=_failed(built.validation, f"rule rejected: {exc}")
                    )
                    self.log[-1]["validation"] = built.validation.model_dump(mode="json")
                else:
                    return RuleOutcome(rule, classified.text, built.files)
            last_validation, last_files = built.validation, built.files
            if built.validation.status is ValidationStatus.NOT_ATTEMPTED:
                break  # the environment cannot validate; asking again will not help
            prompt = prompts.repair_prompt(base, data, built.validation.message or "failed")
        rejected = {f"rejected/{rule_id}/{path}": text for path, text in last_files.items()}
        return RuleOutcome(
            _advice(rule_id, classified, source, last_validation), classified.text,
            rejected_files=rejected,
        )  # fmt: skip

    def _check_action(self, rule_id: str, answer: BaseModel, attempt: int) -> _Built:
        assert isinstance(answer, ActionTranslation)  # noqa: S101  # dispatch invariant
        validation, agy_gaps = validate_permissions(
            answer.claude_code_deny, answer.antigravity_deny, answer.must_deny,
            answer.must_allow, attempts=attempt,
        )  # fmt: skip
        targets: list[PermissionTarget] = []
        if validation.status is ValidationStatus.VERIFIED:
            try:
                targets.append(
                    PermissionTarget(agent=AgentName.CLAUDE_CODE, deny=answer.claude_code_deny)
                )
                if answer.antigravity_deny:
                    targets.append(
                        PermissionTarget(agent=AgentName.ANTIGRAVITY, deny=answer.antigravity_deny)
                    )
            except ValueError as exc:  # entry rejected by the rule format contract
                validation = _failed(validation, f"deny entry rejected by the contract: {exc}")
        gaps = [*answer.known_gaps, *agy_gaps]
        if any(entry.startswith("Read") for entry in answer.claude_code_deny):
            gaps.append(READ_DENY_GAP)
        if answer.antigravity_deny:
            gaps.append(AGY_FILE_GAP)
        examples = {
            "must_deny": [call.model_dump() for call in answer.must_deny],
            "must_allow": [call.model_dump() for call in answer.must_allow],
        }
        validation = _require_gaps(validation, answer.coverage, gaps)
        verified = validation.status is ValidationStatus.VERIFIED
        name = f"examples/{rule_id}/permissions.json" if verified else "permissions.json"
        return _Built(
            validation,
            Targets(permissions=targets),
            _coverage(answer.coverage, gaps),
            gaps,
            {name: json.dumps(examples, indent=2) + "\n"},
        )

    def _check_code(self, rule_id: str, answer: BaseModel, attempt: int) -> _Built:
        assert isinstance(answer, CodeTranslation)  # noqa: S101  # dispatch invariant
        folder = self._fresh(rule_id, attempt)
        rule_file, test_file = folder / f"{rule_id}.yaml", folder / f"{rule_id}.py"
        rule_file.write_text(answer.semgrep_rule, encoding="utf-8")
        test_file.write_text(answer.semgrep_test, encoding="utf-8")
        ids = rule_ids(rule_file)
        if ids != [rule_id]:
            validation = Validation(
                status=ValidationStatus.FAILED, attempts=attempt,
                message=f"the rule file must define exactly one rule {rule_id}, found {ids}",
            )  # fmt: skip
        else:
            validation = validate_semgrep(rule_file, test_file, attempts=attempt)
        validation = _require_gaps(validation, answer.coverage, answer.known_gaps)
        rule_path, test_path = f"semgrep/{rule_id}.yaml", f"semgrep/tests/{rule_id}.py"
        verified = validation.status is ValidationStatus.VERIFIED
        return _Built(
            validation,
            Targets(semgrep=SemgrepTarget(rule_path=rule_path, test_path=test_path)),
            _coverage(answer.coverage, answer.known_gaps),
            list(answer.known_gaps),
            {rule_path if verified else f"{rule_id}.yaml": answer.semgrep_rule,
             test_path if verified else f"{rule_id}.py": answer.semgrep_test},
        )  # fmt: skip

    def _check_behavior(self, rule_id: str, answer: BaseModel, attempt: int) -> _Built:
        assert isinstance(answer, BehaviorTranslation)  # noqa: S101  # dispatch invariant
        folder = self._fresh(rule_id, attempt)
        test_name = f"test_{rule_id.lower().replace('-', '_')}.py"
        test = folder / test_name
        test.write_text(answer.test_file, encoding="utf-8")
        apps = {"secure": answer.secure_app} | {
            f"insecure_{i}": text for i, text in enumerate(answer.insecure_apps, start=1)
        }
        for name, text in apps.items():
            (folder / name).mkdir()
            (folder / name / "app.py").write_text(text, encoding="utf-8")
        neutral = []
        for name, source in NEUTRAL_APPS.items():
            target = folder / f"neutral_{name}"
            shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__"))
            neutral.append(target)
        _readable(folder, self.work)
        validation = self.runner.validate(
            test, [folder / "secure"],
            [folder / n for n in apps if n.startswith("insecure_")],
            neutral=neutral, attempts=attempt,
        )  # fmt: skip
        validation = _require_gaps(validation, answer.coverage, answer.known_gaps)
        test_path = f"tests/security/{test_name}"
        verified = validation.status is ValidationStatus.VERIFIED
        files = {test_path if verified else test_name: answer.test_file}
        prefix = f"examples/{rule_id}/" if verified else ""
        files |= {f"{prefix}{name}/app.py": text for name, text in apps.items()}
        return _Built(
            validation, Targets(pytest=PytestTarget(test_path=test_path)),
            _coverage(answer.coverage, answer.known_gaps), list(answer.known_gaps), files,
        )  # fmt: skip

    def _fresh(self, rule_id: str, attempt: int) -> Path:
        folder = self.work / rule_id / f"attempt-{attempt}"
        folder.mkdir(parents=True)
        return folder


def _failed(validation: Validation, message: str) -> Validation:
    return validation.model_copy(update={"status": ValidationStatus.FAILED, "message": message})


def _require_gaps(validation: Validation, coverage: str, gaps: Sequence[str]) -> Validation:
    if validation.status is ValidationStatus.VERIFIED and coverage == "partial" and not gaps:
        return _failed(validation, "coverage is 'partial' but known_gaps is empty")
    return validation


def _coverage(claim: str, gaps: Sequence[str]) -> Coverage:
    return Coverage.PARTIAL if claim == "partial" or gaps else Coverage.FULL


def _readable(folder: Path, root: Path) -> None:
    """Let the validation container's unprivileged user read the files (no secrets here)."""
    for path in [folder, *folder.rglob("*")]:
        path.chmod(0o755 if path.is_dir() else 0o644)
    for parent in folder.parents:
        if not parent.is_relative_to(root):
            break
        parent.chmod(0o755)


def _advice(
    rule_id: str, classified: ClassifiedRule, source: SourceRef, last: Validation | None
) -> Rule:
    if last is None:
        validation = Validation(status=ValidationStatus.NOT_ATTEMPTED)
    else:
        validation = last
    return Rule(
        id=rule_id,
        source=source,
        category=classified.category,
        cwe=classified.cwe,
        validation=validation,
        enforcement=Enforcement.ADVISE,
        coverage=Coverage.NONE,
    )


def compile_files(
    files: Sequence[Path],
    llm: Llm,
    runner: BehaviorRunner,
    *,
    project_root: Path,
    max_attempts: int = DEFAULT_MAX_ATTEMPTS,
    keyword_filter: bool = True,
    progress: Callable[[str], None] = lambda _: None,
    now: datetime | None = None,
    work_dir: Path | None = None,
) -> CompileResult:
    """Compile instruction files into a ``CompileResult`` (nothing is written yet).

    ``work_dir`` holds the attempts' files while they are validated; a ``DockerRunner``
    must be given the same folder. A temporary folder is used when it is not set.
    """
    root = project_root.resolve()
    if work_dir is not None:
        work_dir.mkdir(parents=True, exist_ok=True)
    sources: list[SourceFile] = []
    outcomes: list[RuleOutcome] = []
    dropped: list[tuple[str, Candidate]] = []
    not_security: list[tuple[str, Candidate]] = []
    left_out: list[tuple[str, Candidate]] = []
    with tempfile.TemporaryDirectory(prefix="sdguard-compile-", dir=work_dir) as tmp:
        session = _Session(llm, runner, Path(tmp), max_attempts, progress)
        counter = 0
        for path in files:
            try:
                relative = path.resolve().relative_to(root).as_posix()
                text = path.read_text(encoding="utf-8")
            except ValueError as exc:
                raise CompileError(f"{path} is outside the project root {root}") from exc
            except (OSError, UnicodeDecodeError) as exc:
                raise CompileError(f"cannot read {path}: {exc}") from exc
            sources.append(SourceFile(path=relative, sha256=_sha256(text)))
            candidates = extract_candidates(text)
            kept = [c for c in candidates if c.looks_security_related or not keyword_filter]
            dropped += [(relative, c) for c in candidates if c not in kept]
            by_line = {c.line: c for c in kept}
            classified, other, skipped = session.classify(relative, kept)
            not_security += [(relative, by_line[line]) for line in sorted(other)]
            left_out += [(relative, by_line[line]) for line in sorted(skipped)]
            for item in classified:
                counter += 1
                rule_id = f"R-{counter:03d}"
                source = SourceRef(
                    file=relative, line=item.source_line, text=by_line[item.source_line].text
                )
                outcomes.append(session.translate(rule_id, item, source))
        log = session.log
    compiled_at = now or datetime.now(UTC)
    ruleset = RuleSet(
        sources=sources,
        compiled_by=CompiledBy(
            agent=AgentName.CLAUDE_CODE, model=llm.model, compiled_at=compiled_at
        ),
        rules=[o.rule for o in outcomes],
    )
    return CompileResult(ruleset, outcomes, dropped, not_security, log, left_out)


def write_package(result: CompileResult, out_dir: Path) -> None:
    """Replace the compiler's own files in ``out_dir``; other files there are kept.

    The package is first written to a sibling temporary folder, so an interrupted write
    never leaves half a package behind.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".sdguard-new-", dir=out_dir.parent))
    try:
        for relative, text in sorted(result.files.items()):
            target = staging / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        for name in MANAGED:
            old = out_dir / name
            if old.is_dir():
                shutil.rmtree(old)
            elif old.exists():
                old.unlink()
            new = staging / name
            if new.exists():
                os.replace(new, old)
    finally:
        shutil.rmtree(staging, ignore_errors=True)


def render_advisory(ruleset: RuleSet) -> str:
    lines = [
        "# Security rules without an automatic check",
        "",
        "sdguard could not turn these rules into verified checks. They still apply.",
        "",
    ]
    for rule in ruleset.advisory:
        lines.append(f"- {rule.source.text} ({rule.id}, {rule.source.file}:{rule.source.line})")
    return "\n".join(lines) + "\n"


def render_report(result: CompileResult) -> str:
    ruleset = result.ruleset
    enforced = ruleset.enforced
    by_category: dict[str, list[Rule]] = {}
    for rule in ruleset.rules:
        by_category.setdefault(rule.category.value, []).append(rule)
    cost = sum(e.get("cost_usd") or 0.0 for e in result.log)
    calls = len(result.log)
    lines = [
        "# sdguard compile report",
        "",
        f"- Sources: {', '.join(f'{s.path} ({s.sha256[:12]})' for s in ruleset.sources)}",
        f"- Model: {ruleset.compiled_by.model}, {ruleset.compiled_by.compiled_at.isoformat()}",
        f"- Model calls: {calls}, reported cost: {cost:.2f} USD",
        f"- Rules: {len(ruleset.rules)}; enforced (verified): {len(enforced)}; "
        f"advice: {len(ruleset.advisory)}",
        "",
        "| Category | Rules | Verified and enforced |",
        "|---|---|---|",
    ]
    for category in RuleCategory:
        rules = by_category.get(category.value, [])
        lines.append(f"| {category.value} | {len(rules)} | {sum(r.is_enforced for r in rules)} |")
    lines += ["", "## Rules", ""]
    for outcome in result.outcomes:
        rule = outcome.rule
        v = rule.validation
        lines += [
            f"### {rule.id} · {rule.category.value} · {rule.enforcement.value}",
            "",
            f"- Source: {rule.source.file}:{rule.source.line}: {rule.source.text}",
            f"- Read as: {outcome.restated}",
            f"- CWE: {', '.join(rule.cwe) or '-'}",
            f"- Validation: {v.status.value}, {v.good_examples} good / {v.bad_examples} bad "
            f"examples, {v.attempts} attempt(s)",
        ]
        if v.message:
            lines.append(f"- Validator: {v.message}")
        if rule.coverage is not Coverage.NONE:
            lines.append(f"- Coverage: {rule.coverage.value}")
        lines += [f"- Known gap: {gap}" for gap in rule.known_gaps]
        lines.append("")
    if result.left_out:
        lines += ["## Not classified by the model (check by hand)", ""]
        lines += [f"- {f}:{c.line}: {c.text}" for f, c in result.left_out]
        lines.append("")
    if result.not_security:
        lines += ["## Not security rules (model)", ""]
        lines += [f"- {f}:{c.line}: {c.text}" for f, c in result.not_security]
        lines.append("")
    if result.dropped:
        lines += ["## Left out by the keyword filter", ""]
        lines += [f"- {f}:{c.line}: {c.text}" for f, c in result.dropped]
        lines.append("")
    return "\n".join(lines)
