#!/usr/bin/env python3
"""Spike 2b (PostInvocation): after the model's tool calls, inject a message if SQL is unsafe.

At most MAX_INJECTS times per conversation so a stubborn agent cannot loop forever.
"""

import sys

import sdspike

MAX_INJECTS = 3

if __name__ == "__main__":
    data = sdspike.read_input()
    issues = sdspike.sql_issues(sdspike.workspace(data))
    if not issues or sdspike.bump_counter(data, "inject") > MAX_INJECTS:
        sys.exit(sdspike.reply({}))
    message = "sdguard deneme: SQL injection riski. " + "; ".join(issues) + ". " + sdspike.SQL_RULE
    sys.exit(sdspike.reply({"injectSteps": [{"ephemeralMessage": message}]}))
