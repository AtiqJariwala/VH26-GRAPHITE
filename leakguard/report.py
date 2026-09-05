"""Enhanced reporting with beautiful visual output using rich."""

from dataclasses import dataclass
from typing import List

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from .confidence import Confidence


@dataclass
class LeakFinding:
    """A single resource leak finding."""
    
    file_path: str
    acquisition_line: int
    resource_type: str
    resource_expr: str
    confidence: Confidence
    explanation: str
    
    def format(self) -> str:
        """Format this finding for human output."""
        return (
            f"[{self.confidence.value.upper()}] {self.file_path}:{self.acquisition_line}\n"
            f"  Resource: {self.resource_type} ({self.resource_expr})\n"
            f"  {self.explanation}"
        )


class Report:
    """Collection of findings and summary statistics with enhanced visuals."""
    
    def __init__(self):
        self.findings: List[LeakFinding] = []
        self.console = Console() if HAS_RICH else None
    
    def add(self, finding: LeakFinding):
        """Add a finding to the report."""
        self.findings.append(finding)
    
    def count_by_confidence(self, confidence: Confidence) -> int:
        """Count findings at a specific confidence level."""
        return sum(1 for f in self.findings if f.confidence == confidence)
    
    def has_failures(self, threshold: Confidence) -> bool:
        """Check if any findings meet or exceed the threshold."""
        return any(f.confidence.should_fail(threshold) for f in self.findings)
    
    def print_summary(self):
        """Print a beautiful summary with rich formatting if available."""
        if HAS_RICH and self.console:
            self._print_rich_summary()
        else:
            self._print_plain_summary()
    
    def _print_rich_summary(self):
        """Print summary with rich formatting."""
        console = self.console
        
        if not self.findings:
            console.print(Panel.fit(
                "[bold green]No resource leaks detected[/bold green]",
                border_style="green"
            ))
            return
        
        # Header
        console.print()
        console.print(Panel.fit(
            f"[bold red]Found {len(self.findings)} potential resource leak(s)[/bold red]",
            border_style="red"
        ))
        console.print()
        
        # Findings table
        table = Table(title="Leak Details", show_header=True, header_style="bold cyan")
        table.add_column("Severity", style="bold", width=12)
        table.add_column("Location", style="cyan")
        table.add_column("Resource Type", style="yellow")
        table.add_column("Issue", style="white")
        
        for finding in self.findings:
            severity_style = {
                Confidence.DEFINITELY: "[bold red]DEFINITELY[/bold red]",
                Confidence.LIKELY: "[bold yellow]LIKELY[/bold yellow]",
                Confidence.POSSIBLE: "[bold blue]POSSIBLE[/bold blue]"
            }[finding.confidence]
            
            location = f"{finding.file_path}:{finding.acquisition_line}"
            resource = f"{finding.resource_type}\n({finding.resource_expr})"
            
            table.add_row(
                severity_style,
                location,
                resource,
                finding.explanation
            )
        
        console.print(table)
        console.print()
        
        # Summary statistics
        definitely = self.count_by_confidence(Confidence.DEFINITELY)
        likely = self.count_by_confidence(Confidence.LIKELY)
        possible = self.count_by_confidence(Confidence.POSSIBLE)
        
        summary_table = Table(title="Summary Statistics", show_header=True, header_style="bold magenta")
        summary_table.add_column("Confidence Level", style="bold")
        summary_table.add_column("Count", justify="right", style="bold")
        
        if definitely > 0:
            summary_table.add_row("[red]Definitely leaked[/red]", f"[red]{definitely}[/red]")
        else:
            summary_table.add_row("Definitely leaked", "0")
            
        if likely > 0:
            summary_table.add_row("[yellow]Likely leaked[/yellow]", f"[yellow]{likely}[/yellow]")
        else:
            summary_table.add_row("Likely leaked", "0")
            
        if possible > 0:
            summary_table.add_row("[blue]Possibly leaked[/blue]", f"[blue]{possible}[/blue]")
        else:
            summary_table.add_row("Possibly leaked", "0")
        
        console.print(summary_table)
        console.print()
    
    def _print_plain_summary(self):
        """Print plain text summary (fallback)."""
        if not self.findings:
            print("✓ No resource leaks detected")
            return
        
        print(f"\n⚠ Found {len(self.findings)} potential resource leak(s):\n")
        
        for finding in self.findings:
            print(finding.format())
            print()
        
        definitely = self.count_by_confidence(Confidence.DEFINITELY)
        likely = self.count_by_confidence(Confidence.LIKELY)
        possible = self.count_by_confidence(Confidence.POSSIBLE)
        
        print("Summary:")
        print(f"  Definitely leaked: {definitely}")
        print(f"  Likely leaked: {likely}")
        print(f"  Possibly leaked: {possible}")
