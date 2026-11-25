"""Applications that a compiled behavior test must not report a finding on.

A behavior test runs against the agent's application, which neither the test nor the
compiler knows. A test whose assertions check more than its rule (for example "an unknown
route answers 404") would block the agent for code that follows the rule. Each compiled
test therefore also runs against these apps; an ``assertion`` outcome on any of them fails
the validation. ``error`` (a failed ``require``) and ``passed`` are fine.

- ``minimal``: no accounts and no uploads; a page and a POST endpoint that accepts any
  request and ignores files (a test that takes every 200 for an accepted upload fails here).
- ``guarded``: accounts with hashed passwords, signed JWTs with a pinned algorithm, every
  request except registration and login needs a token (unknown routes answer 401, as many
  real apps with a global guard do), a per-user note store, errors without internals.
"""

from pathlib import Path

NEUTRAL_APPS: dict[str, Path] = {
    name: Path(__file__).parent / name for name in ("minimal", "guarded")
}
