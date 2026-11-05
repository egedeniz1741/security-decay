#!/usr/bin/env python3
"""Spike 4: save the payload, then print something that is not JSON (exit 0)."""

import sys

import sdspike

if __name__ == "__main__":
    sdspike.read_input()
    print("bu JSON degil {")
    sys.exit(0)
