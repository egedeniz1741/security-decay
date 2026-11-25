"""Masking of the login token before anything reaches the disk.

The token sits in the agent's environment, and the agent's commands and app can read it
(harness/docker/README.md, V8c), so every log and the turn's files are checked for it.
"""

MASK = "***sd-masked***"


def mask(text: str, secrets: list[str]) -> tuple[str, int]:
    """The text with each secret replaced, and how many replacements were made."""
    count = 0
    for secret in secrets:
        if secret:
            count += text.count(secret)
            text = text.replace(secret, MASK)
    return text, count
