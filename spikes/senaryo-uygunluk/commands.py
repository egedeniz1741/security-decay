"""Across all agy runs: which tools and which shell programs the agent used (for a fixed allow list)."""
import collections
import json
import pathlib
import re
import shlex
import sys

root = pathlib.Path(sys.argv[1])
tools: collections.Counter[str] = collections.Counter()
programs: collections.Counter[str] = collections.Counter()
runs_using: collections.defaultdict[str, set[str]] = collections.defaultdict(set)
compound = 0
total_cmds = 0
for out in sorted(root.glob("*/r[0-9]/out/out.jsonl")):
    run = f"{out.parts[-4]}/{out.parts[-3]}"
    for line in out.open():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        su = e.get("step_update") or {}
        if su.get("step_type") != "tool" or su.get("state") not in ("DONE", "ERROR"):
            continue
        name = su.get("tool_name", "?")
        tools[name] += 1
        runs_using[name].add(run)
        cmd = (su.get("tool_info", {}).get("parameters", {}) or {}).get("CommandLine")
        if not cmd:
            continue
        total_cmds += 1
        try:
            lex = shlex.shlex(cmd, posix=True, punctuation_chars=True)
            lex.whitespace_split = True
            tokens = list(lex)
        except ValueError:
            tokens = cmd.split()
        ops = {"&&", "||", ";", "|", "&"}
        starts = [0] + [i + 1 for i, t in enumerate(tokens) if t in ops]
        if len(starts) > 1:
            compound += 1
        for i in starts:
            if i < len(tokens) and tokens[i] not in ops:
                prog = pathlib.Path(tokens[i]).name
                programs[prog] += 1
                runs_using["cmd:" + prog].add(run)
n_runs = len({r for s in runs_using.values() for r in s})
print(f"runs: {n_runs}")
print("tools (calls, runs):", {t: (c, len(runs_using[t])) for t, c in tools.most_common()})
print(f"shell commands: {total_cmds}, compound (&&, ;, |): {compound}")
print("programs (calls, runs):", {p: (c, len(runs_using['cmd:' + p])) for p, c in programs.most_common()})
