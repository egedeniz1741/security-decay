# Antigravity CLI hook inputs (fixtures)

Real JSON inputs that Antigravity CLI (`agy` 1.5.1, model `gemini-3.8-flash-high`) sent to hooks
during the G0 experiments on 2026-11-05 (`spikes/antigravity/`). Conversation ids are replaced
with `00000000-…` and `/root` with `/home/user`. Used as test data for the adapters.

agy does not put the event name in the payload; the file name gives it.

| File | Event | Spike step | Notes |
|---|---|---|---|
| `pretooluse-read-file-env.json` | PreToolUse / `read_file` | 01B | Denied by the `.env` rule |
| `pretooluse-run-command-cat-env.json` | PreToolUse / `run_command` | 01C | `cat .env`, denied |
| `pretooluse-run-command-grep-bypass.json` | PreToolUse / `run_command` | 01D | `grep -rnI "API_KEY" .`, no `.env` in the input, so the name-based rule let it through |
| `posttooluse-edit-file.json` | PostToolUse / `edit_file` | 02P | Has `toolCall` (not in the docs), no tool output |
| `preinvocation.json` | PreInvocation | 01B | |
| `postinvocation.json` | PostInvocation | 02I | Same shape as PreInvocation |
| `stop.json` | Stop | 03H | `terminationReason: "NO_TOOL_CALL"` |
