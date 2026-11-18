"""Split the scenario pool into 2 development and 4 test scenarios, at random but reproducibly.

Only splits where both sides contain every required CWE are allowed; one of them is drawn with
the given seed. The seed is written down (and approved) before this is run, so the split cannot
be redrawn until it looks convenient.

Usage: python split.py pool.json SEED
pool.json: {"Forum": [79, 89], ...}  (BaxBench CWEs of each scenario's security tests)
"""

import itertools
import json
import random
import sys

REQUIRED_CWES = {79, 89}
N_DEV = 2


def valid_dev_sets(pool: dict[str, set[int]]) -> list[tuple[str, ...]]:
    names = sorted(pool)
    result = []
    for dev in itertools.combinations(names, N_DEV):
        test = [n for n in names if n not in dev]
        dev_cwes = set().union(*(pool[n] for n in dev))
        test_cwes = set().union(*(pool[n] for n in test))
        if REQUIRED_CWES <= dev_cwes and REQUIRED_CWES <= test_cwes:
            result.append(dev)
    return result


def main() -> None:
    pool = {name: set(cwes) for name, cwes in json.load(open(sys.argv[1])).items()}
    seed = int(sys.argv[2])
    options = valid_dev_sets(pool)
    dev = random.Random(seed).choice(options)
    test = sorted(n for n in pool if n not in dev)
    print(f"pool: {sorted(pool)}")
    print(f"valid development pairs: {len(options)} of {len(list(itertools.combinations(pool, N_DEV)))}")
    print(f"seed: {seed}")
    print(f"development: {list(dev)}")
    print(f"test: {test}")
    print(f"scenario 1: {sorted(dev)[0]}")


if __name__ == "__main__":
    main()
