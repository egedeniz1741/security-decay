# Claude Code hook inputs (fixtures)

Real JSON inputs that Claude Code sent to hooks during the G0 experiments, with personal
data removed (user name, session ids). Used as test data for the adapters.

| File | Event | Recorded | Notes |
|---|---|---|---|
| `pretooluse-bash-grep-bypass.json` | PreToolUse / Bash | 2026-11-03, Claude Code 2.1.317 | G0 spike 1 step D: `grep -rn` over the folder, no `.env` in the input, so the name-based rule let it through |
