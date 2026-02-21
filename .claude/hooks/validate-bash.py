#!/usr/bin/env python3
"""
PreToolUse Hook: Validates Bash commands before execution.
Blocks dangerous commands that could harm the system or data.

Exit codes:
  0 - Allow command
  2 - Block command (stderr shown to user)
"""
import json
import sys
import re

# Read input from stdin
try:
    input_data = json.load(sys.stdin)
except json.JSONDecodeError:
    sys.exit(0)  # Allow if can't parse

tool_name = input_data.get("tool_name", "")
if tool_name != "Bash":
    sys.exit(0)

command = input_data.get("tool_input", {}).get("command", "")

# Dangerous patterns to block
DANGEROUS_PATTERNS = [
    # Destructive file operations
    (r"rm\s+-rf\s+/(?!\w)", "BLOCKED: 'rm -rf /' is extremely dangerous"),
    (r"rm\s+-rf\s+~", "BLOCKED: 'rm -rf ~' would delete home directory"),
    (r"rm\s+-rf\s+\*", "BLOCKED: 'rm -rf *' in root is dangerous"),

    # Database destruction
    (r"drop\s+database", "BLOCKED: DROP DATABASE detected"),
    (r"truncate\s+table", "BLOCKED: TRUNCATE TABLE detected - use DELETE with WHERE"),

    # Git dangerous operations
    (r"git\s+push\s+.*--force\s+.*(?:main|master)", "BLOCKED: Force push to main/master"),
    (r"git\s+reset\s+--hard\s+HEAD~\d{2,}", "BLOCKED: Hard reset of many commits"),

    # System destruction
    (r"mkfs\.", "BLOCKED: Filesystem format command detected"),
    (r"dd\s+.*of=/dev/", "BLOCKED: Direct disk write detected"),

    # Credential exposure
    (r"curl.*-d.*password", "WARNING: Password in curl command - consider using env vars"),

    # Docker volume destruction (LLARS-specific)
    (r"docker\s+volume\s+rm\s+.*llars", "BLOCKED: Removing LLARS volumes - use 'docker compose down -v' instead"),
]

# Check command against patterns
for pattern, message in DANGEROUS_PATTERNS:
    if re.search(pattern, command, re.IGNORECASE):
        print(message, file=sys.stderr)
        if message.startswith("BLOCKED"):
            sys.exit(2)  # Block the command
        # Warnings (exit 0) are logged but don't block

sys.exit(0)  # Allow command
