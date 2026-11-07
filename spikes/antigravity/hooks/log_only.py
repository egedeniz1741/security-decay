#!/usr/bin/env python3
"""Save the payload and return an empty object (no opinion). Used to record what each event sends."""

import sys

import sdspike

if __name__ == "__main__":
    sdspike.read_input()
    sys.exit(sdspike.reply({}))
