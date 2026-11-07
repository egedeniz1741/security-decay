#!/usr/bin/env python3
"""Spike 4: save the payload, then sleep past the hook timeout (set to 3 s in hooks.json)."""

import sys
import time

import sdspike

if __name__ == "__main__":
    sdspike.read_input()
    time.sleep(20)
    sys.exit(sdspike.reply({}))
