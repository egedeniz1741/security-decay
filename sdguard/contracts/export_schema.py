"""Write the JSON Schema of the rule format next to the code.

Run after changing ``rules.py``:  uv run python -m sdguard.contracts.export_schema
"""

import json
from pathlib import Path

from sdguard.contracts.rules import ruleset_json_schema

SCHEMA_FILE = Path(__file__).parent / "schema" / "ruleset.schema.json"


def main() -> None:
    SCHEMA_FILE.write_text(json.dumps(ruleset_json_schema(), indent=2, sort_keys=True) + "\n")
    print(f"wrote {SCHEMA_FILE}")


if __name__ == "__main__":
    main()
