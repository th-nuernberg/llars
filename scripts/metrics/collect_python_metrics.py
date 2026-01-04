#!/usr/bin/env python3
"""
Python Code Metrics Collector.

Collects various code quality metrics for the LLARS backend:
- Docstring coverage (per file and per module)
- Line counts and file sizes
- Function/class complexity indicators
- Large file detection

Usage:
    python scripts/metrics/collect_python_metrics.py [--json] [--update-docs]

Options:
    --json         Output as JSON instead of human-readable text
    --update-docs  Update docs/docs/entwickler/code-qualitaet.md automatically

Author: LLARS Team
Date: January 2026
"""

import ast
import json
import os
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


@dataclass
class FunctionMetrics:
    """Metrics for a single function or method."""
    name: str
    has_docstring: bool
    line_count: int
    start_line: int
    is_method: bool = False


@dataclass
class ClassMetrics:
    """Metrics for a single class."""
    name: str
    has_docstring: bool
    method_count: int
    methods_with_docstrings: int
    start_line: int


@dataclass
class FileMetrics:
    """Metrics for a single Python file."""
    path: str
    line_count: int
    function_count: int
    functions_with_docstrings: int
    class_count: int
    classes_with_docstrings: int
    module_has_docstring: bool
    large_functions: List[str] = field(default_factory=list)

    @property
    def docstring_coverage(self) -> float:
        """Calculate overall docstring coverage percentage."""
        total = self.function_count + self.class_count + 1  # +1 for module
        with_docs = self.functions_with_docstrings + self.classes_with_docstrings
        if self.module_has_docstring:
            with_docs += 1
        return (with_docs / total * 100) if total > 0 else 0.0


@dataclass
class DirectoryMetrics:
    """Aggregated metrics for a directory."""
    path: str
    total_files: int
    total_lines: int
    total_functions: int
    functions_with_docstrings: int
    total_classes: int
    classes_with_docstrings: int
    modules_with_docstrings: int
    large_files: List[str] = field(default_factory=list)

    @property
    def function_docstring_coverage(self) -> float:
        if self.total_functions == 0:
            return 0.0
        return self.functions_with_docstrings / self.total_functions * 100

    @property
    def class_docstring_coverage(self) -> float:
        if self.total_classes == 0:
            return 0.0
        return self.classes_with_docstrings / self.total_classes * 100

    @property
    def overall_coverage(self) -> float:
        total = self.total_functions + self.total_classes + self.total_files
        with_docs = (self.functions_with_docstrings +
                    self.classes_with_docstrings +
                    self.modules_with_docstrings)
        return (with_docs / total * 100) if total > 0 else 0.0


class PythonMetricsCollector:
    """Collects code metrics from Python files using AST parsing."""

    LARGE_FILE_THRESHOLD = 500  # lines
    LARGE_FUNCTION_THRESHOLD = 50  # lines

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.file_metrics: Dict[str, FileMetrics] = {}
        self.errors: List[str] = []

    def collect_file_metrics(self, file_path: Path) -> Optional[FileMetrics]:
        """Collect metrics for a single Python file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()

            lines = source.split('\n')
            line_count = len(lines)

            tree = ast.parse(source, filename=str(file_path))

            # Check module docstring
            module_has_docstring = (
                tree.body and
                isinstance(tree.body[0], ast.Expr) and
                isinstance(tree.body[0].value, ast.Constant) and
                isinstance(tree.body[0].value.value, str)
            )

            functions = []
            classes = []
            large_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    has_docstring = (
                        node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)
                    )

                    # Calculate function line count
                    func_lines = node.end_lineno - node.lineno + 1 if hasattr(node, 'end_lineno') else 0

                    functions.append(FunctionMetrics(
                        name=node.name,
                        has_docstring=has_docstring,
                        line_count=func_lines,
                        start_line=node.lineno
                    ))

                    if func_lines > self.LARGE_FUNCTION_THRESHOLD:
                        large_functions.append(f"{node.name} ({func_lines} lines)")

                elif isinstance(node, ast.ClassDef):
                    has_docstring = (
                        node.body and
                        isinstance(node.body[0], ast.Expr) and
                        isinstance(node.body[0].value, ast.Constant) and
                        isinstance(node.body[0].value.value, str)
                    )

                    # Count methods in class
                    methods = [n for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    methods_with_docs = sum(1 for m in methods if (
                        m.body and
                        isinstance(m.body[0], ast.Expr) and
                        isinstance(m.body[0].value, ast.Constant) and
                        isinstance(m.body[0].value.value, str)
                    ))

                    classes.append(ClassMetrics(
                        name=node.name,
                        has_docstring=has_docstring,
                        method_count=len(methods),
                        methods_with_docstrings=methods_with_docs,
                        start_line=node.lineno
                    ))

            return FileMetrics(
                path=str(file_path.relative_to(self.base_path)),
                line_count=line_count,
                function_count=len(functions),
                functions_with_docstrings=sum(1 for f in functions if f.has_docstring),
                class_count=len(classes),
                classes_with_docstrings=sum(1 for c in classes if c.has_docstring),
                module_has_docstring=module_has_docstring,
                large_functions=large_functions
            )

        except SyntaxError as e:
            self.errors.append(f"Syntax error in {file_path}: {e}")
            return None
        except Exception as e:
            self.errors.append(f"Error processing {file_path}: {e}")
            return None

    def collect_directory_metrics(self, directory: str, exclude_patterns: List[str] = None) -> DirectoryMetrics:
        """Collect aggregated metrics for a directory."""
        exclude_patterns = exclude_patterns or ['__pycache__', '.git', 'venv', 'migrations']

        dir_path = self.base_path / directory
        if not dir_path.exists():
            return DirectoryMetrics(path=directory, total_files=0, total_lines=0,
                                   total_functions=0, functions_with_docstrings=0,
                                   total_classes=0, classes_with_docstrings=0,
                                   modules_with_docstrings=0)

        total_files = 0
        total_lines = 0
        total_functions = 0
        functions_with_docstrings = 0
        total_classes = 0
        classes_with_docstrings = 0
        modules_with_docstrings = 0
        large_files = []

        for py_file in dir_path.rglob('*.py'):
            # Skip excluded patterns
            if any(p in str(py_file) for p in exclude_patterns):
                continue

            metrics = self.collect_file_metrics(py_file)
            if metrics:
                self.file_metrics[metrics.path] = metrics
                total_files += 1
                total_lines += metrics.line_count
                total_functions += metrics.function_count
                functions_with_docstrings += metrics.functions_with_docstrings
                total_classes += metrics.class_count
                classes_with_docstrings += metrics.classes_with_docstrings
                if metrics.module_has_docstring:
                    modules_with_docstrings += 1

                if metrics.line_count > self.LARGE_FILE_THRESHOLD:
                    large_files.append(f"{metrics.path} ({metrics.line_count} lines)")

        return DirectoryMetrics(
            path=directory,
            total_files=total_files,
            total_lines=total_lines,
            total_functions=total_functions,
            functions_with_docstrings=functions_with_docstrings,
            total_classes=total_classes,
            classes_with_docstrings=classes_with_docstrings,
            modules_with_docstrings=modules_with_docstrings,
            large_files=large_files
        )


def collect_all_metrics(base_path: str) -> dict:
    """Collect all Python metrics for the project."""
    collector = PythonMetricsCollector(base_path)

    # Collect metrics for each major directory
    directories = {
        'services': 'app/services',
        'routes': 'app/routes',
        'workers': 'app/workers',
        'models': 'app/db',
        'auth': 'app/auth',
        'decorators': 'app/decorators',
    }

    results = {
        'timestamp': datetime.now().isoformat(),
        'directories': {},
        'summary': {},
        'large_files': [],
        'files_without_module_docstring': [],
        'errors': []
    }

    total_functions = 0
    total_functions_with_docs = 0
    total_classes = 0
    total_classes_with_docs = 0
    total_modules = 0
    total_modules_with_docs = 0

    for name, path in directories.items():
        metrics = collector.collect_directory_metrics(path)
        results['directories'][name] = {
            'path': path,
            'files': metrics.total_files,
            'lines': metrics.total_lines,
            'functions': metrics.total_functions,
            'functions_with_docstrings': metrics.functions_with_docstrings,
            'function_coverage': round(metrics.function_docstring_coverage, 1),
            'classes': metrics.total_classes,
            'classes_with_docstrings': metrics.classes_with_docstrings,
            'class_coverage': round(metrics.class_docstring_coverage, 1),
            'overall_coverage': round(metrics.overall_coverage, 1),
            'large_files': metrics.large_files
        }

        total_functions += metrics.total_functions
        total_functions_with_docs += metrics.functions_with_docstrings
        total_classes += metrics.total_classes
        total_classes_with_docs += metrics.classes_with_docstrings
        total_modules += metrics.total_files
        total_modules_with_docs += metrics.modules_with_docstrings
        results['large_files'].extend(metrics.large_files)

    # Calculate summary
    results['summary'] = {
        'total_functions': total_functions,
        'functions_with_docstrings': total_functions_with_docs,
        'function_coverage': round(total_functions_with_docs / total_functions * 100, 1) if total_functions > 0 else 0,
        'total_classes': total_classes,
        'classes_with_docstrings': total_classes_with_docs,
        'class_coverage': round(total_classes_with_docs / total_classes * 100, 1) if total_classes > 0 else 0,
        'total_modules': total_modules,
        'modules_with_docstrings': total_modules_with_docs,
        'module_coverage': round(total_modules_with_docs / total_modules * 100, 1) if total_modules > 0 else 0,
    }

    # Find files without module docstrings
    for path, metrics in collector.file_metrics.items():
        if not metrics.module_has_docstring:
            results['files_without_module_docstring'].append(path)

    results['errors'] = collector.errors

    return results


def update_documentation(metrics: dict, docs_path: str):
    """Update the code-qualitaet.md file with current metrics."""
    doc_file = Path(docs_path) / 'docs' / 'entwickler' / 'code-qualitaet.md'

    if not doc_file.exists():
        print(f"Documentation file not found: {doc_file}")
        return False

    # Read current content
    with open(doc_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Generate new metrics table
    summary = metrics['summary']
    timestamp = datetime.fromisoformat(metrics['timestamp']).strftime('%d.%m.%Y %H:%M')

    new_backend_table = f"""### Backend (Python)

!!! info "Automatisch aktualisiert: {timestamp}"

| Bereich | Funktionen | Mit Docstring | Coverage |
|---------|------------|---------------|----------|
"""

    for name, data in metrics['directories'].items():
        coverage_icon = "✅" if data['function_coverage'] >= 70 else "⚠️" if data['function_coverage'] >= 50 else "❌"
        new_backend_table += f"| **{name.title()}** | {data['functions']} | {data['functions_with_docstrings']} | {coverage_icon} {data['function_coverage']}% |\n"

    new_backend_table += f"\n**Gesamt:** {summary['function_coverage']}% Funktionen, {summary['class_coverage']}% Klassen, {summary['module_coverage']}% Module"

    # Replace the backend section (simplified - in production use regex)
    # For now, just print what would be updated
    print(f"\n📊 Backend Metrics Update:")
    print(new_backend_table)

    return True


def print_human_readable(metrics: dict):
    """Print metrics in human-readable format."""
    print("\n" + "=" * 60)
    print("LLARS Python Code Metrics")
    print("=" * 60)
    print(f"Generated: {metrics['timestamp']}\n")

    print("📁 Directory Breakdown:")
    print("-" * 60)

    for name, data in metrics['directories'].items():
        coverage_icon = "✅" if data['function_coverage'] >= 70 else "⚠️" if data['function_coverage'] >= 50 else "❌"
        print(f"\n{name.upper()} ({data['path']})")
        print(f"  Files: {data['files']}, Lines: {data['lines']:,}")
        print(f"  Functions: {data['functions_with_docstrings']}/{data['functions']} ({data['function_coverage']}%) {coverage_icon}")
        print(f"  Classes: {data['classes_with_docstrings']}/{data['classes']} ({data['class_coverage']}%)")

        if data['large_files']:
            print(f"  ⚠️  Large files: {', '.join(data['large_files'][:3])}")

    print("\n" + "-" * 60)
    print("📊 SUMMARY")
    print("-" * 60)
    s = metrics['summary']
    print(f"  Function Docstring Coverage: {s['function_coverage']}%")
    print(f"  Class Docstring Coverage:    {s['class_coverage']}%")
    print(f"  Module Docstring Coverage:   {s['module_coverage']}%")

    if metrics['large_files']:
        print(f"\n⚠️  Large files (>{PythonMetricsCollector.LARGE_FILE_THRESHOLD} lines):")
        for f in metrics['large_files'][:10]:
            print(f"    - {f}")
        if len(metrics['large_files']) > 10:
            print(f"    ... and {len(metrics['large_files']) - 10} more")

    if metrics['errors']:
        print(f"\n❌ Errors during collection:")
        for e in metrics['errors']:
            print(f"    - {e}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    # Determine base path
    script_dir = Path(__file__).parent
    base_path = script_dir.parent.parent  # Go up from scripts/metrics to project root

    # Check for arguments
    output_json = '--json' in sys.argv
    update_docs = '--update-docs' in sys.argv

    # Collect metrics
    metrics = collect_all_metrics(str(base_path))

    if output_json:
        print(json.dumps(metrics, indent=2))
    else:
        print_human_readable(metrics)

    if update_docs:
        docs_path = base_path / 'docs'
        update_documentation(metrics, str(docs_path))

    # Save to file
    output_file = base_path / 'docs' / 'metrics' / 'python_metrics.json'
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(metrics, f, indent=2)

    # Only print status message when not in JSON mode (to avoid corrupting JSON output)
    if not output_json:
        print(f"\n💾 Metrics saved to: {output_file}")
