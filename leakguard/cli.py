"""Enhanced command-line interface with beautiful output."""

import argparse
import sys
from pathlib import Path
from typing import List

try:
    from rich.console import Console
    from rich.progress import track
    from rich.panel import Panel
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from .analyzer import analyze_file
from .confidence import Confidence
from .report import Report


console = Console() if HAS_RICH else None


def find_python_files(path: Path) -> List[Path]:
    """Recursively find all Python files in a directory."""
    if path.is_file():
        if path.suffix == ".py":
            return [path]
        return []
    
    py_files = []
    for item in path.rglob("*.py"):
        if item.is_file():
            py_files.append(item)
    return py_files


def scan_command(args):
    """Execute the scan command with beautiful output."""
    path = Path(args.path)
    
    if not path.exists():
        if HAS_RICH and console:
            console.print(f"[bold red]Error:[/bold red] Path does not exist: {path}")
        else:
            print(f"Error: Path does not exist: {path}", file=sys.stderr)
        return 1
    
    files = find_python_files(path)
    
    if not files:
        if HAS_RICH and console:
            console.print(f"[yellow]No Python files found in {path}[/yellow]")
        else:
            print(f"No Python files found in {path}")
        return 0
    
    # Header
    if HAS_RICH and console:
        console.print()
        console.print(Panel.fit(
            f"[bold cyan]LeakGuard Scanner[/bold cyan]\n"
            f"Scanning {len(files)} Python file(s)...",
            border_style="cyan"
        ))
        console.print()
    else:
        print(f"\nScanning {len(files)} Python file(s)...\n")
    
    # Analyze files with progress bar
    report = Report()
    
    if HAS_RICH:
        file_iterator = track(files, description="[cyan]Analyzing files...", console=console)
    else:
        file_iterator = files
        
    for py_file in file_iterator:
        try:
            file_findings = analyze_file(py_file)
            for finding in file_findings:
                report.add(finding)
        except SyntaxError as e:
            if HAS_RICH and console:
                console.print(f"[yellow]Syntax error in {py_file}: {e}[/yellow]")
            else:
                print(f"Syntax error in {py_file}: {e}", file=sys.stderr)
        except Exception as e:
            if HAS_RICH and console:
                console.print(f"[red]Error analyzing {py_file}: {e}[/red]")
            else:
                print(f"Error analyzing {py_file}: {e}", file=sys.stderr)
    
    # Print results
    report.print_summary()
    
    # Determine exit code
    threshold = args.fail_on
    if report.has_failures(threshold):
        if HAS_RICH and console:
            console.print(Panel.fit(
                f"[bold red]Build failed: found leaks at or above '{threshold.value}' confidence level[/bold red]",
                border_style="red"
            ))
        else:
            print(f"\nBuild failed: found leaks at or above '{threshold.value}' confidence level")
        return 1
    
    return 0


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="leakguard",
        description="LeakGuard - Static resource-leak detector for Python",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
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
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    if args.command == "scan":
        return scan_command(args)
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
