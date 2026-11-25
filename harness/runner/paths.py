"""Protected path list (harness/protected_paths.json) and path matching.

Paths are compared after normalization to the agent container's view: relative paths are
taken from /work, ``~`` and ``$HOME`` are expanded and ``..`` is collapsed
(02_DENEY_ALTYAPISI.md §4).
"""

import hashlib
import json
import posixpath
import re
from dataclasses import dataclass
from functools import cache
from pathlib import Path

WORK = "/work"
HOME = "/home/agent"
PROTECTED_PATHS_FILE = Path(__file__).resolve().parents[1] / "protected_paths.json"


def normalize(path: str, *, cwd: str = WORK, home: str = HOME) -> str:
    if path == "~" or path.startswith("~/"):
        path = home + path[1:]
    elif path == "$HOME" or path.startswith("$HOME/"):
        path = home + path[5:]
    if not path.startswith("/"):
        path = posixpath.join(cwd, path)
    return posixpath.normpath(path)


@cache
def _pattern(glob: str) -> re.Pattern[str]:
    """``**`` spans directories, ``*`` and ``?`` do not; ``dir/**`` also matches ``dir``."""
    glob = normalize(glob) if glob.startswith(("~", "/")) else glob
    tail = ""
    if glob.endswith("/**"):
        glob, tail = glob[:-3], "(/.*)?"
    out = []
    i = 0
    while i < len(glob):
        if glob.startswith("**", i):
            out.append(".*")
            i += 2
        elif glob[i] == "*":
            out.append("[^/]*")
            i += 1
        elif glob[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(glob[i]))
            i += 1
    return re.compile("".join(out) + tail)


def matches(path: str, globs: tuple[str, ...]) -> bool:
    """Whether a normalized path matches any of the globs."""
    return any(_pattern(g).fullmatch(path) for g in globs)


@dataclass(frozen=True)
class ProtectedPaths:
    settings_and_hooks: tuple[str, ...]
    credentials: tuple[str, ...]
    exceptions: tuple[str, ...]
    integrity: tuple[str, ...]
    integrity_json_keys: dict[str, tuple[str, ...]]
    rule_and_test_files: tuple[str, ...]
    sha256: str

    def is_protected(self, path: str) -> bool:
        """A path whose access counts toward ``protected_read_attempts``."""
        return matches(path, self.settings_and_hooks + self.credentials) and not matches(
            path, self.exceptions
        )

    def is_rule_or_test(self, path: str) -> bool:
        return matches(path, self.rule_and_test_files)


def load(path: Path = PROTECTED_PATHS_FILE) -> ProtectedPaths:
    raw = path.read_bytes()
    data = json.loads(raw)
    return ProtectedPaths(
        settings_and_hooks=tuple(data["settings_and_hooks"]),
        credentials=tuple(data["credentials"]),
        exceptions=tuple(data["exceptions"]),
        integrity=tuple(data["integrity"]),
        integrity_json_keys={k: tuple(v) for k, v in data["integrity_json_keys"].items()},
        rule_and_test_files=tuple(data["rule_and_test_files"]),
        sha256=hashlib.sha256(raw).hexdigest(),
    )
