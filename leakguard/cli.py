"""Command-line interface for LeakGuard."""

import argparse
import sys
from pathlib import Path
from typing import List

from .analyzer import analyze_file
from .confidence import Confidence
from .report import Report


def find_python_files(path: Path) -> List[Path]:
    """Recursively find all Python files in a directory."""
    if path.is_file():
        if path.suffix == ".py":
            return [path]
        return []
    
    # Directory: find all .py files recursively
    py_files = []
    for item in path.rglob("*.py"):
        if item.is_file():
            py_files.append(item)
    return py_files


def scan_command(args):
    """Execute the scan command."""
    path = Path(args.path)
    
    if not path.exists():
        print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 1
    
    # Find all Python files to scan
    files = find_python_files(path)
    
    if not files:
        print(f"No Python files found in {path}")
        return 0
    
    print(f"Scanning {len(files)} Python file(s)...")
    
    # Analyze each file
    report = Report()
    for py_file in files:
        try:
            file_findings = analyze_file(py_file)
            for finding in file_findings:
                report.add(finding)
        except SyntaxError as e:
            print(f"Syntax error in {py_file}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"Error analyzing {py_file}: {e}", file=sys.stderr)
    
    # Print results
    report.print_summary()
    
    # Determine exit code based on threshold
    threshold = args.fail_on
    if report.has_failures(threshold):
        print(f"\nBuild failed: found leaks at or above '{threshold}' confidence level")
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="leakguard",
        description="Static resource-leak detector for Python code",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # scan command
    scan_parser = subparsers.add_parser("scan", help="Scan Python files for resource leaks")
    scan_parser.add_argument(
        "path",
        help="File or directory to scan"
    )
    scan_parser.add_argument(
        "--fail-on",
        type=lambda s: Confidence.from_string(s),
        default=Confidence.LIKELY,
        choices=list(Confidence),
        help="Confidence level at which to fail the build (default: likely)"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "scan":
        return scan_command(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
