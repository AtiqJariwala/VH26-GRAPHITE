"""Reporting and output formatting for leak findings."""

from dataclasses import dataclass
from typing import List
from .confidence import Confidence


@dataclass
class LeakFinding:
    """A single resource leak finding."""
    
    file_path: str
    acquisition_line: int
    resource_type: str
    resource_expr: str  # The actual expression, e.g., "open('file.txt')"
    confidence: Confidence
    explanation: str  # Why this is considered a leak
    
    def format(self) -> str:
        """Format this finding for human output."""
        return (
            f"[{self.confidence.value.upper()}] {self.file_path}:{self.acquisition_line}\n"
            f"  Resource: {self.resource_type} ({self.resource_expr})\n"
            f"  {self.explanation}"
        )


class Report:
    """Collection of findings and summary statistics."""
    
    def __init__(self):
        self.findings: List[LeakFinding] = []
    
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
        """Print a human-readable summary."""
        if not self.findings:
            print("No resource leaks detected")
            return
        
        print(f"\nFound {len(self.findings)} potential resource leak(s):\n")
        
        for finding in self.findings:
            print(finding.format())
            print()
        
        # Summary by confidence
        definitely = self.count_by_confidence(Confidence.DEFINITELY)
        likely = self.count_by_confidence(Confidence.LIKELY)
        possible = self.count_by_confidence(Confidence.POSSIBLE)
        
        print("Summary:")
        print(f"  Definitely leaked: {definitely}")
        print(f"  Likely leaked: {likely}")
        print(f"  Possibly leaked: {possible}")
