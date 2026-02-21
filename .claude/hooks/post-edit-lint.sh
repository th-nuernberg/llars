#!/bin/bash
# PostToolUse Hook: Run linting after file edits
# Only runs for Python and JavaScript/Vue files

set -e

# Read input from stdin
INPUT=$(cat)

# Extract file path from the tool input
FILE_PATH=$(echo "$INPUT" | python3 -c "
import json, sys
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('file_path', ''))
" 2>/dev/null)

if [ -z "$FILE_PATH" ]; then
    exit 0
fi

# Get file extension
EXT="${FILE_PATH##*.}"

# Run appropriate linter based on file type
case "$EXT" in
    py)
        # Python: Run flake8 if available (non-blocking)
        if command -v flake8 &> /dev/null; then
            flake8 "$FILE_PATH" --max-line-length=120 --ignore=E501,W503 2>/dev/null || true
        fi
        ;;
    js|vue|ts|tsx)
        # JavaScript/Vue: Run eslint if available (non-blocking)
        if [ -f "$CLAUDE_PROJECT_DIR/llars-frontend/node_modules/.bin/eslint" ]; then
            cd "$CLAUDE_PROJECT_DIR/llars-frontend"
            ./node_modules/.bin/eslint "$FILE_PATH" --fix 2>/dev/null || true
        fi
        ;;
esac

exit 0
