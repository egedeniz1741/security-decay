#!/usr/bin/env python3
"""Spike 4: save the payload, then fail on purpose (exit 1, nothing on stdout)."""

import sys

import sdspike

if __name__ == "__main__":
    sdspike.read_input()
    print("sdguard deneme: hook bilerek coktu", file=sys.stderr)
    sys.exit(1)
