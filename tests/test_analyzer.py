"""Unit tests for the leak analyzer."""

import pytest
from pathlib import Path
from leakguard.analyzer import analyze_file
from leakguard.confidence import Confidence


def test_simple_file_leak():
    """Test detection of simple file leak."""
    findings = analyze_file(Path("tests/fixtures/leaky/01_simple_file_leak.py"))
    assert len(findings) == 1
    assert findings[0].confidence == Confidence.DEFINITELY
    assert findings[0].resource_type == "file"
    assert "open('data.txt', 'r')" in findings[0].resource_expr


def test_context_manager_safe():
    """Test that context managers are recognized as safe."""
    findings = analyze_file(Path("tests/fixtures/clean/01_with_statement.py"))
    # Should have no DEFINITELY or LIKELY findings
    serious_findings = [f for f in findings if f.confidence in (Confidence.DEFINITELY, Confidence.LIKELY)]
    assert len(serious_findings) == 0


def test_explicit_close_safe():
    """Test that explicit close() is recognized as safe."""
    findings = analyze_file(Path("tests/fixtures/clean/02_explicit_close.py"))
    serious_findings = [f for f in findings if f.confidence in (Confidence.DEFINITELY, Confidence.LIKELY)]
    assert len(serious_findings) == 0


def test_try_finally_safe():
    """Test that try/finally is recognized as safe."""
    findings = analyze_file(Path("tests/fixtures/clean/03_try_finally.py"))
    serious_findings = [f for f in findings if f.confidence in (Confidence.DEFINITELY, Confidence.LIKELY)]
    assert len(serious_findings) == 0


def test_socket_leak():
    """Test detection of socket leak."""
    findings = analyze_file(Path("tests/fixtures/leaky/04_socket_leak.py"))
    assert len(findings) == 1
    assert findings[0].confidence == Confidence.DEFINITELY
    assert findings[0].resource_type == "socket"


def test_database_leak():
    """Test detection of database connection leak."""
    findings = analyze_file(Path("tests/fixtures/leaky/05_database_leak.py"))
    assert len(findings) == 1
    assert findings[0].confidence == Confidence.DEFINITELY
    assert findings[0].resource_type == "database"


def test_reassignment_leak():
    """Test detection of variable reassignment leak."""
    findings = analyze_file(Path("tests/fixtures/leaky/06_reassignment_leak.py"))
    assert len(findings) == 1
    assert findings[0].confidence == Confidence.POSSIBLE
    assert "reassigned" in findings[0].explanation


def test_early_return_leak():
    """Test detection of leak via early return."""
    findings = analyze_file(Path("tests/fixtures/leaky/02_early_return_leak.py"))
    assert len(findings) == 1
    assert findings[0].confidence == Confidence.LIKELY
    assert findings[0].resource_type == "file"


def test_multiple_leaks():
    """Test detection of multiple different resource leaks in one file."""
    findings = analyze_file(Path("tests/fixtures/leaky/09_multiple_leaks.py"))
    # Should find file, socket, and database leaks
    assert len(findings) == 3
    resource_types = {f.resource_type for f in findings}
    assert "file" in resource_types
    assert "socket" in resource_types
    assert "database" in resource_types


def test_lock_with_context_manager_safe():
    """Test that lock in context manager is safe."""
    findings = analyze_file(Path("tests/fixtures/clean/08_lock_with_context.py"))
    serious_findings = [f for f in findings if f.confidence in (Confidence.DEFINITELY, Confidence.LIKELY)]
    assert len(serious_findings) == 0


def test_lock_leak():
    """Test detection of lock leak."""
    findings = analyze_file(Path("tests/fixtures/leaky/10_lock_leak.py"))
    assert len(findings) == 1
    assert findings[0].resource_type == "lock"


def test_no_resources():
    """Test file with no resources doesn't trigger false positives."""
    findings = analyze_file(Path("tests/fixtures/clean/10_no_resources.py"))
    assert len(findings) == 0


def test_passed_to_function():
    """Test resource passed to unknown function gives ownership_unknown."""
    findings = analyze_file(Path("tests/fixtures/leaky/08_passed_to_unknown_function.py"))
    assert len(findings) == 1
    assert findings[0].confidence == Confidence.POSSIBLE
    assert "ownership" in findings[0].explanation.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
