#!/usr/bin/env python3
"""
Documentation Metrics Updater.

Reads collected metrics and updates the mkdocs documentation automatically.

Usage:
    python scripts/metrics/update_docs.py

This script:
1. Reads metrics from docs/metrics/*.json
2. Updates docs/docs/entwickler/code-qualitaet.md
3. Updates relevant sections with current data

Author: LLARS Team
Date: January 2026
"""

import json
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def load_metrics(metrics_dir: Path) -> dict:
    """Load all metrics files."""
    metrics = {}

    python_file = metrics_dir / 'python_metrics.json'
    if python_file.exists():
        with open(python_file, 'r', encoding='utf-8') as f:
            metrics['python'] = json.load(f)

    frontend_file = metrics_dir / 'frontend_metrics.json'
    if frontend_file.exists():
        with open(frontend_file, 'r', encoding='utf-8') as f:
            metrics['frontend'] = json.load(f)

    test_coverage_file = metrics_dir / 'test_coverage.json'
    if test_coverage_file.exists():
        with open(test_coverage_file, 'r', encoding='utf-8') as f:
            metrics['tests'] = json.load(f)

    return metrics


def get_coverage_icon(coverage: float) -> str:
    """Return emoji based on coverage percentage."""
    if coverage >= 70:
        return "✅"
    elif coverage >= 50:
        return "⚠️"
    else:
        return "❌"


def generate_backend_section(python_metrics: dict) -> str:
    """Generate the Backend metrics section."""
    timestamp = datetime.fromisoformat(python_metrics['timestamp']).strftime('%d.%m.%Y %H:%M')
    summary = python_metrics['summary']

    section = f"""### Backend (Python)

!!! info "Automatisch aktualisiert: {timestamp}"

| Bereich | Funktionen | Mit Docstring | Coverage |
|---------|------------|---------------|----------|
"""

    for name, data in python_metrics['directories'].items():
        icon = get_coverage_icon(data['function_coverage'])
        section += f"| **{name.title()}** | {data['functions']} | {data['functions_with_docstrings']} | {icon} {data['function_coverage']}% |\n"

    overall_icon = get_coverage_icon(summary['function_coverage'])
    section += f"""
**Gesamt:** {overall_icon} {summary['function_coverage']}% Funktionen, {summary['class_coverage']}% Klassen, {summary['module_coverage']}% Module
"""

    return section


def generate_frontend_section(frontend_metrics: dict) -> str:
    """Generate the Frontend metrics section."""
    timestamp = datetime.fromisoformat(frontend_metrics['timestamp']).strftime('%d.%m.%Y %H:%M')
    summary = frontend_metrics['summary']

    section = f"""### Frontend (Vue.js)

!!! info "Automatisch aktualisiert: {timestamp}"

| Bereich | Dateien | Mit JSDoc | Coverage |
|---------|---------|-----------|----------|
"""

    for name, data in frontend_metrics['directories'].items():
        icon = get_coverage_icon(data['coverage'])
        section += f"| **{name.title()}** | {data['files']} | {data['filesWithJSDoc']} | {icon} {data['coverage']}% |\n"

    overall_icon = get_coverage_icon(summary['coverage'])
    section += f"""
**Gesamt:** {overall_icon} {summary['coverage']}% der Dateien haben JSDoc-Header
"""

    return section


def generate_test_coverage_section(test_metrics: dict) -> str:
    """Generate the Test Coverage section."""
    section = """### Test Coverage

| Bereich | Coverage | Status |
|---------|----------|--------|
"""

    if 'backend' in test_metrics:
        be = test_metrics['backend']
        icon = get_coverage_icon(be['coverage'])
        section += f"| **Backend Unit Tests** | {be['coverage']}% | {icon} |\n"

    if 'frontend' in test_metrics:
        fe = test_metrics['frontend']
        icon = get_coverage_icon(fe['coverage'])
        section += f"| **Frontend Tests** | {fe['coverage']}% | {icon} |\n"

    return section


def generate_large_files_section(python_metrics: dict, frontend_metrics: dict) -> str:
    """Generate the Large Files section."""
    section = """### Große Dateien (Refactoring-Kandidaten)

#### Backend (>500 Zeilen)

| Datei | Zeilen |
|-------|--------|
"""

    if python_metrics.get('large_files'):
        for f in python_metrics['large_files'][:10]:
            # Parse "path (N lines)" format
            match = re.match(r'(.+) \((\d+) lines\)', f)
            if match:
                section += f"| `{match.group(1)}` | {match.group(2)} |\n"
    else:
        section += "| *(Keine großen Dateien)* | - |\n"

    section += """
#### Frontend (>500 Zeilen)

| Datei | Zeilen |
|-------|--------|
"""

    if frontend_metrics.get('largeFiles'):
        for f in frontend_metrics['largeFiles'][:10]:
            match = re.match(r'(.+) \((\d+) lines\)', f)
            if match:
                section += f"| `{match.group(1)}` | {match.group(2)} |\n"
    else:
        section += "| *(Keine großen Dateien)* | - |\n"

    return section


def update_documentation(metrics: dict, docs_path: Path):
    """Update the code-qualitaet.md file."""
    doc_file = docs_path / 'docs' / 'entwickler' / 'code-qualitaet.md'

    if not doc_file.exists():
        print(f"❌ Documentation file not found: {doc_file}")
        return False

    # Read current content
    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate new sections
    new_content = content

    # Update Backend section
    if 'python' in metrics:
        backend_section = generate_backend_section(metrics['python'])
        # Replace existing backend section
        pattern = r'### Backend \(Python\).*?(?=### Frontend|### Test Coverage|### Kritische Bereiche|---|\Z)'
        if re.search(pattern, new_content, re.DOTALL):
            new_content = re.sub(pattern, backend_section + '\n', new_content, flags=re.DOTALL)

    # Update Frontend section
    if 'frontend' in metrics:
        frontend_section = generate_frontend_section(metrics['frontend'])
        pattern = r'### Frontend \(Vue\.js\).*?(?=### Test Coverage|### Kritische Bereiche|---|\Z)'
        if re.search(pattern, new_content, re.DOTALL):
            new_content = re.sub(pattern, frontend_section + '\n', new_content, flags=re.DOTALL)

    # Write updated content
    with open(doc_file, 'w', encoding='utf-8') as f:
        f.write(new_content)

    print(f"✅ Updated: {doc_file}")
    return True


def run_pytest_coverage(project_path: Path) -> dict:
    """Run pytest with coverage and return results."""
    try:
        result = subprocess.run(
            ['pytest', 'tests/', '--cov=app', '--cov-report=json', '-q', '--tb=no'],
            cwd=project_path,
            capture_output=True,
            text=True,
            timeout=300
        )

        coverage_file = project_path / 'coverage.json'
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                data = json.load(f)
                return {
                    'backend': {
                        'coverage': round(data.get('totals', {}).get('percent_covered', 0), 1),
                        'lines_covered': data.get('totals', {}).get('covered_lines', 0),
                        'lines_total': data.get('totals', {}).get('num_statements', 0),
                    }
                }
    except Exception as e:
        print(f"⚠️  Could not run pytest coverage: {e}")

    return {}


def run_vitest_coverage(frontend_path: Path) -> dict:
    """Run vitest with coverage and return results."""
    try:
        result = subprocess.run(
            ['npm', 'run', 'test:coverage', '--', '--reporter=json'],
            cwd=frontend_path,
            capture_output=True,
            text=True,
            timeout=300
        )

        coverage_file = frontend_path / 'coverage' / 'coverage-summary.json'
        if coverage_file.exists():
            with open(coverage_file, 'r') as f:
                data = json.load(f)
                total = data.get('total', {})
                return {
                    'frontend': {
                        'coverage': round(total.get('lines', {}).get('pct', 0), 1),
                        'lines_covered': total.get('lines', {}).get('covered', 0),
                        'lines_total': total.get('lines', {}).get('total', 0),
                    }
                }
    except Exception as e:
        print(f"⚠️  Could not run vitest coverage: {e}")

    return {}


def main():
    """Main function."""
    script_dir = Path(__file__).parent
    project_path = script_dir.parent.parent
    docs_path = project_path / 'docs'
    metrics_dir = docs_path / 'metrics'

    print("📊 Loading metrics...")
    metrics = load_metrics(metrics_dir)

    if not metrics:
        print("❌ No metrics found. Run collect_python_metrics.py and collect_frontend_metrics.js first.")
        sys.exit(1)

    print(f"  Found: {', '.join(metrics.keys())}")

    # Optionally run tests and collect coverage
    if '--run-tests' in sys.argv:
        print("\n🧪 Running test coverage...")
        test_metrics = {}

        # Backend
        backend_coverage = run_pytest_coverage(project_path)
        test_metrics.update(backend_coverage)

        # Frontend
        frontend_path = project_path / 'llars-frontend'
        frontend_coverage = run_vitest_coverage(frontend_path)
        test_metrics.update(frontend_coverage)

        if test_metrics:
            metrics['tests'] = test_metrics
            # Save test metrics
            with open(metrics_dir / 'test_coverage.json', 'w') as f:
                json.dump(test_metrics, f, indent=2)
            print(f"  Backend: {test_metrics.get('backend', {}).get('coverage', 'N/A')}%")
            print(f"  Frontend: {test_metrics.get('frontend', {}).get('coverage', 'N/A')}%")

    print("\n📝 Updating documentation...")
    update_documentation(metrics, docs_path)

    print("\n✅ Done!")


if __name__ == '__main__':
    main()
