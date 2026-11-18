"""Summarize one agy stream-json run: tool calls, durations, model, final status."""
import json, sys
model, steps, result = None, [], None
for line in open(sys.argv[1]):
    try:
        e = json.loads(line)
    except json.JSONDecodeError:
        continue
    if e.get("event") == "init":
        model = e["init"].get("model") or e["init"].get("model_name")
    su = e.get("step_update") or {}
    if su.get("step_type") == "tool" and su.get("state") in ("DONE", "ERROR"):
        info = su.get("tool_info", {})
        p = info.get("parameters", {})
        arg = p.get("CommandLine") or p.get("TargetFile") or p.get("AbsolutePath") or p.get("path") or ""
        steps.append((su.get("tool_name"), su["state"], round(su.get("duration_seconds") or 0, 1), str(arg)[:110]))
    if e.get("event") == "result":
        result = e["result"]
print("model:", model)
for s in steps:
    print("  ", *s)
if result:
    print("status:", result.get("status"), "turns:", result.get("num_turns"), "dur:", round(result.get("duration_seconds", 0)), "usage:", result.get("usage"))
    print("response:", (result.get("response") or "")[:300].replace("\n", " "))
