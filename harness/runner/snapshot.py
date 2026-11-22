"""Hashes of the integrity files, taken inside the agent container (stdlib only).

The runner sends this file's source with ``python3 -c`` before and after each turn, so no
measurement code stays in the container for the agent to find (R22). Argument: a JSON
object ``{"globs": [...], "json_keys": {path: [key, ...]}}`` with ``~`` already expanded.
Output: a JSON object mapping each file (or ``path#key``) to its sha256.
"""

import glob
import hashlib
import json
import os
import sys


def snapshot(globs: list[str], json_keys: dict[str, list[str]]) -> dict[str, str]:
    hashes = {}
    for pattern in globs:
        for path in glob.glob(pattern, recursive=True, include_hidden=True):
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    hashes[path] = hashlib.sha256(f.read()).hexdigest()
    for path, keys in json_keys.items():
        try:
            with open(path) as f:
                data = json.load(f)
        except (OSError, ValueError):
            continue
        for key in keys:
            if key in data:
                value = json.dumps(data[key], sort_keys=True).encode()
                hashes[f"{path}#{key}"] = hashlib.sha256(value).hexdigest()
    return hashes


def changes(before: dict[str, str], after: dict[str, str]) -> list[str]:
    """Files added, removed or changed between two snapshots."""
    return sorted(p for p in set(before) | set(after) if before.get(p) != after.get(p))


if __name__ == "__main__":
    spec = json.loads(sys.argv[1])
    print(json.dumps(snapshot(spec["globs"], spec["json_keys"]), sort_keys=True))
