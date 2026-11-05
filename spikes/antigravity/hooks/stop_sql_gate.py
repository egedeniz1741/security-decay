#!/usr/bin/env python3
"""Spike 3 (Stop): do not let the agent finish while unsafe SQL remains (at most MAX_BLOCKS times)."""

import sys

import sdspike

MAX_BLOCKS = 3

if __name__ == "__main__":
    data = sdspike.read_input()
    issues = sdspike.sql_issues(sdspike.workspace(data))
    if not issues:
        sys.exit(sdspike.reply({}))
    if sdspike.bump_counter(data, "stop-blocks") > MAX_BLOCKS:
        sys.exit(sdspike.reply({}))
    message = "sdguard deneme: SQL injection riski. " + "; ".join(issues) + ". " + sdspike.SQL_RULE
    sys.exit(sdspike.reply({"decision": "continue", "reason": message}))
