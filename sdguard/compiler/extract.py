"""Split an instruction file (AGENTS.md, CLAUDE.md) into candidate rule statements.

This is the deterministic first step of ``sdguard compile`` (docs/plan/01_MIMARI.md §2.1).
Every list item and every plain paragraph becomes a ``Candidate`` with its line number and
the headings above it. Code blocks, tables, HTML comments and front matter are skipped:
they hold examples and configuration, not rules.

A light keyword filter marks the candidates that look security related. The LLM still
classifies every candidate it is given; the filter only keeps obviously unrelated lines
(formatting, commit style) out of the prompt, and the report lists what it dropped, so
nothing is lost silently.
"""

import re
from dataclasses import dataclass

_HEADING = re.compile(r"^(?P<hashes>#{1,6})\s+(?P<text>.+?)\s*#*\s*$")
_LIST_ITEM = re.compile(r"^(?P<indent>\s*)(?:[-*+]|\d{1,3}[.)])\s+(?P<text>.*)$")
_FENCE = re.compile(r"^\s*(```|~~~)")
_TABLE = re.compile(r"^\s*\|")
_CHECKBOX = re.compile(r"^\[[ xX]\]\s+")

# Lower-case stems; a candidate matches when any stem occurs in its text or headings.
# English and Turkish, because the corpus and our own rule files use both.
SECURITY_STEMS: tuple[str, ...] = (
    # general
    "secur",
    "güvenl",
    "vulnerab",
    "zafiyet",
    "attack",
    "saldır",
    "exploit",
    "owasp",
    "cwe",
    # secrets and credentials
    "secret",
    "gizli",
    "password",
    "parola",
    "şifre",
    "credential",
    "token",
    "api key",
    "api_key",
    "apikey",
    "private key",
    ".env",
    "environment variable",
    "ortam değişken",
    # authentication and authorization
    "auth",
    "login",
    "giriş",
    "session",
    "oturum",
    "permission",
    "izin",
    "admin",
    "yönetici",
    "role",
    "rol",
    "privilege",
    "yetki",
    "access control",
    "erişim",
    "owner",
    "sahip",
    "jwt",
    "cookie",
    "csrf",
    "cors",
    # injection and input handling
    "sql",
    "inject",
    "enjeksiyon",
    "xss",
    "escape",
    "sanitiz",
    "validat",
    "doğrula",
    "untrusted",
    "user input",
    "kullanıcı girdi",
    "eval",
    "exec",
    "pickle",
    "deserializ",
    "shell",
    "subprocess",
    "command",
    "komut",
    # files, network, crypto, configuration
    "upload",
    "yükle",
    "path travers",
    "file path",
    "dosya yol",
    "redirect",
    "ssrf",
    "url",
    "encrypt",
    "şifrele",
    "hash",
    "crypt",
    "tls",
    "https",
    "certificate",
    "random",
    "debug",
    "stack trace",
    "log",
    "rate limit",
    "dependenc",
    "bağımlılık",
    "package",
    "paket",
    "pip install",
    "npm install",
    "delete",
    "sil",
    "rm -rf",
    "force push",
)


@dataclass(frozen=True)
class Candidate:
    """One statement of the instruction file that may be a rule."""

    line: int  # 1-based line of the first line of the statement
    text: str  # the statement with Markdown list markers removed, continuation lines joined
    headings: tuple[str, ...] = ()  # enclosing headings, outermost first

    @property
    def looks_security_related(self) -> bool:
        haystack = " ".join((*self.headings, self.text)).lower()
        return any(stem in haystack for stem in SECURITY_STEMS)


def _clean(text: str) -> str:
    text = _CHECKBOX.sub("", text.strip())
    return re.sub(r"\s+", " ", text).strip()


def extract_candidates(markdown: str) -> list[Candidate]:
    """Return list items and paragraphs of ``markdown`` in document order."""
    candidates: list[Candidate] = []
    headings: list[tuple[int, str]] = []  # (level, text)
    current: list[str] = []
    current_line = 0
    in_fence = in_comment = False
    lines = markdown.splitlines()

    def flush() -> None:
        nonlocal current
        text = _clean(" ".join(current))
        if text:
            candidates.append(Candidate(current_line, text, tuple(h for _, h in headings)))
        current = []

    start = 0
    if lines and lines[0].strip() == "---":  # YAML front matter
        for index in range(1, len(lines)):
            if lines[index].strip() in ("---", "..."):
                start = index + 1
                break

    for number, raw in enumerate(lines[start:], start=start + 1):
        stripped = raw.strip()
        if in_comment:
            if "-->" in stripped:
                in_comment = False
            continue
        if _FENCE.match(raw):
            flush()
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if stripped.startswith("<!--"):
            flush()
            in_comment = "-->" not in stripped
            continue
        heading = _HEADING.match(raw)
        if heading:
            flush()
            level = len(heading["hashes"])
            headings = [(lvl, text) for lvl, text in headings if lvl < level]
            headings.append((level, _clean(heading["text"])))
            continue
        if not stripped or _TABLE.match(raw) or set(stripped) <= set("-=*_ "):
            flush()
            continue
        item = _LIST_ITEM.match(raw)
        if item:
            flush()
            current, current_line = [item["text"]], number
            continue
        if current:  # continuation of a list item or paragraph
            current.append(stripped)
        else:
            current, current_line = [stripped], number
    flush()
    return candidates
