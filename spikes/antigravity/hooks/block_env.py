#!/usr/bin/env python3
"""Spike 1 and 5 (PreToolUse): deny any tool call whose arguments mention a .env file.

Otherwise answer "ask", which leaves the call to the normal permission rules. An empty {}
would deny it (step 01E), and "allow" would skip the permission rules.
"""

import json
import re
import sys

import sdspike

ENV_PATTERN = re.compile(r"""(?:^|[\s/'"=])\.env(?:$|[\s.'"/;|&)])""")

if __name__ == "__main__":
    data = sdspike.read_input()
    args = (data.get("toolCall") or {}).get("args") or {}
    if ENV_PATTERN.search(json.dumps(args)):
        sys.exit(sdspike.reply({
            "decision": "deny",
            "reason": "sdguard deneme: .env dosyasina erisim proje kurali ile yasak.",
        }))
    sys.exit(sdspike.reply({"decision": "ask"}))
