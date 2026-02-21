#!/bin/bash
# =============================================================================
# LLARS Metrics Collection Script
# =============================================================================
# Collects all code quality metrics and optionally updates documentation.
#
# Usage:
#   ./scripts/metrics/collect_all.sh [--update-docs] [--run-tests]
#
# Options:
#   --update-docs  Update docs/docs/entwickler/code-qualitaet.md
#   --run-tests    Run test coverage (slower)
#   --json         Output JSON only (for CI/CD)
#
# Author: LLARS Team
# Date: January 2026
# =============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Parse arguments
UPDATE_DOCS=false
RUN_TESTS=false
JSON_OUTPUT=false

for arg in "$@"; do
    case $arg in
        --update-docs)
            UPDATE_DOCS=true
            ;;
        --run-tests)
            RUN_TESTS=true
            ;;
        --json)
            JSON_OUTPUT=true
            ;;
    esac
done

echo "========================================"
echo "LLARS Code Metrics Collection"
echo "========================================"
echo "Project: $PROJECT_DIR"
echo "Date: $(date)"
echo ""

# Create metrics directory
mkdir -p "$PROJECT_DIR/docs/metrics"

# Collect Python metrics
echo "📊 Collecting Python metrics..."
cd "$PROJECT_DIR"
if [ "$JSON_OUTPUT" = true ]; then
    python3 "$SCRIPT_DIR/collect_python_metrics.py" --json
else
    python3 "$SCRIPT_DIR/collect_python_metrics.py"
fi

# Collect Frontend metrics
echo ""
echo "📊 Collecting Frontend metrics..."
if command -v node &> /dev/null; then
    cd "$PROJECT_DIR"
    if [ "$JSON_OUTPUT" = true ]; then
        node "$SCRIPT_DIR/collect_frontend_metrics.js" --json
    else
        node "$SCRIPT_DIR/collect_frontend_metrics.js"
    fi
else
    echo "⚠️  Node.js not found, skipping frontend metrics"
fi

# Run tests if requested
if [ "$RUN_TESTS" = true ]; then
    echo ""
    echo "🧪 Running test coverage..."

    # Backend tests
    echo "  Running pytest..."
    cd "$PROJECT_DIR"
    if command -v pytest &> /dev/null; then
        pytest tests/ --cov=app --cov-report=json --cov-report=term-missing -q --tb=no 2>/dev/null || true

        if [ -f "coverage.json" ]; then
            COVERAGE=$(python3 -c "import json; print(json.load(open('coverage.json'))['totals']['percent_covered'])" 2>/dev/null || echo "0")
            echo "  ✅ Backend coverage: ${COVERAGE}%"
        fi
    else
        echo "  ⚠️  pytest not found"
    fi

    # Frontend tests
    echo "  Running vitest..."
    cd "$PROJECT_DIR/llars-frontend"
    if [ -f "package.json" ]; then
        npm run test:coverage --silent 2>/dev/null || true

        if [ -f "coverage/coverage-summary.json" ]; then
            COVERAGE=$(node -e "console.log(require('./coverage/coverage-summary.json').total.lines.pct)" 2>/dev/null || echo "0")
            echo "  ✅ Frontend coverage: ${COVERAGE}%"
        fi
    fi
fi

# Update documentation if requested
if [ "$UPDATE_DOCS" = true ]; then
    echo ""
    echo "📝 Updating documentation..."
    cd "$PROJECT_DIR"

    if [ "$RUN_TESTS" = true ]; then
        python3 "$SCRIPT_DIR/update_docs.py" --run-tests
    else
        python3 "$SCRIPT_DIR/update_docs.py"
    fi
fi

echo ""
echo "========================================"
echo "✅ Metrics collection complete!"
echo "========================================"
echo ""
echo "Metrics saved to: $PROJECT_DIR/docs/metrics/"
echo ""

# Summary
if [ -f "$PROJECT_DIR/docs/metrics/python_metrics.json" ]; then
    echo "Python Metrics:"
    python3 -c "
import json
with open('$PROJECT_DIR/docs/metrics/python_metrics.json') as f:
    m = json.load(f)
    s = m['summary']
    print(f\"  Function Coverage: {s['function_coverage']}%\")
    print(f\"  Class Coverage: {s['class_coverage']}%\")
    print(f\"  Module Coverage: {s['module_coverage']}%\")
"
fi

if [ -f "$PROJECT_DIR/docs/metrics/frontend_metrics.json" ]; then
    echo ""
    echo "Frontend Metrics:"
    node -e "
const m = require('$PROJECT_DIR/docs/metrics/frontend_metrics.json');
console.log('  JSDoc Coverage: ' + m.summary.coverage + '%');
console.log('  Total Files: ' + m.summary.totalFiles);
"
fi
