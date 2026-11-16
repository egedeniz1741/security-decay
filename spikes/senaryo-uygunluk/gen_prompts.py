"""Write BaxBench's own agent-mode turn-1 prompt (Python-Flask, OpenAPI spec, no safety prompt).

Run from the BaxBench checkout with its virtualenv (see README.md):
    .venv/bin/python gen_prompts.py <out_dir> <Scenario> [<Scenario> ...]
"""

import pathlib
import sys

sys.path.insert(0, "src")

import docker  # noqa: E402

# BaxBench's scenario modules open a Docker client at import time; prompts do not need one.
docker.from_env = lambda *a, **k: None

from env.python import FlaskEnv  # noqa: E402
from scenarios import all_scenarios  # noqa: E402

out = pathlib.Path(sys.argv[1])
wanted = set(sys.argv[2:])
out.mkdir(parents=True, exist_ok=True)
for scenario in all_scenarios:
    if scenario.id in wanted:
        text = scenario.build_prompt(FlaskEnv, "openapi", "none", agent=True)
        (out / f"{scenario.id}.txt").write_text(text)
        print(scenario.id, len(text), "chars")
