"""Scenarios the runner knows (SENARYO_SECIMI.md, ADR-0019).

Only development scenarios live in this repo; the test split stays in the private repo until
G3 (ADR-0017).
"""

from dataclasses import dataclass
from pathlib import Path

from sdguard.contracts.turns import Split

PROMPTS_DIR = Path(__file__).resolve().parents[1] / "prompts"


@dataclass(frozen=True)
class Scenario:
    id: str  # "S1", as in the turn record
    name: str  # folder under harness/prompts/
    baxbench: str  # BaxBench scenario id, as the exploits name it
    split: Split
    turns: int

    def prompt_file(self, turn: int, prompts_dir: Path = PROMPTS_DIR) -> Path:
        return prompts_dir / self.name / f"turn-{turn}.txt"


SCENARIOS = {
    "S1": Scenario("S1", "credit_card_service", "CreditCardService", Split.DEV, 5),
}
