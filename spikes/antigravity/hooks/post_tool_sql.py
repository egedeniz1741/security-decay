#!/usr/bin/env python3
"""Spike 2a (PostToolUse): if a .py file now builds SQL from strings, try to tell the agent.

The docs say PostToolUse must return {}. This hook deliberately returns a message anyway
(several shapes at once) to see whether any of it reaches the agent.
"""

import sys

import sdspike

if __name__ == "__main__":
    data = sdspike.read_input()
    issues = sdspike.sql_issues(sdspike.workspace(data))
    if not issues:
        sys.exit(sdspike.reply({}))
    message = "sdguard deneme: SQL injection riski. " + "; ".join(issues) + ". " + sdspike.SQL_RULE
    print(message, file=sys.stderr)
    sdspike.reply({
        "decision": "block",
        "reason": message,
        "injectSteps": [{"ephemeralMessage": message}],
    })
    sys.exit(2)
