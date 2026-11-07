#!/usr/bin/env python3
"""Spike 1E-1H (PreToolUse): answer every tool call the same way, to see what "no opinion" means.

argv[2] picks the answer: empty -> {}, silent -> no stdout at all, otherwise {"decision": argv[2]}.
"""

import sys

import sdspike

if __name__ == "__main__":
    sdspike.read_input(tag=sys.argv[2])
    mode = sys.argv[2]
    if mode == "silent":
        sys.exit(0)
    sys.exit(sdspike.reply({} if mode == "empty" else {"decision": mode}))
