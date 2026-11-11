"""Write the JSON Schemas of the contracts next to the code.

Run after changing a contract:  uv run python -m sdguard.contracts.export_schema
"""

import json
from pathlib import Path

from sdguard.contracts.events import HookLogEntry
from sdguard.contracts.rules import ruleset_json_schema
from sdguard.contracts.turns import TurnRecord

SCHEMA_DIR = Path(__file__).parent / "schema"
SCHEMA_FILE = SCHEMA_DIR / "ruleset.schema.json"


def schemas() -> dict[Path, dict[str, object]]:
    return {
        SCHEMA_FILE: ruleset_json_schema(),
        SCHEMA_DIR / "hooklog.schema.json": HookLogEntry.model_json_schema(),
        SCHEMA_DIR / "turn.schema.json": TurnRecord.model_json_schema(),
    }


def main() -> None:
    for path, schema in schemas().items():
        path.write_text(json.dumps(schema, indent=2, sort_keys=True) + "\n")
        print(f"wrote {path}")


if __name__ == "__main__":
    main()
