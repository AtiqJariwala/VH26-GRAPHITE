"""
Seed the dashboard database with demo scan data
Run this once to have data visible on first dashboard load
"""

import sys
import sqlite3
import json
from pathlib import Path
from datetime import datetime

# Add parent to path to import leakguard
sys.path.insert(0, str(Path(__file__).parent.parent))
from leakguard.analyzer import analyze_file

DB_PATH = Path("dashboard/db/scans.db")

def seed_database():
    """Populate database with scans from test fixtures"""
    
    # Ensure database exists
    from dashboard.main import init_db
    init_db()
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Scan all leaky fixtures
    leaky_dir = Path("tests/fixtures/leaky")
    if not leaky_dir.exists():
        print("Test fixtures not found. Run from project root.")
        return
    
    findings = []
    for py_file in leaky_dir.glob("*.py"):
        try:
            file_findings = analyze_file(py_file)
            for finding in file_findings:
                findings.append({
                    'file': str(finding.file_path),
                    'line': finding.acquisition_line,
                    'resource_type': finding.resource_type,
                    'resource_expr': finding.resource_expr,
                    'confidence': finding.confidence.value,
                    'explanation': finding.explanation
                })
        except Exception as e:
            print(f"Error analyzing {py_file}: {e}")
    
    # Count by confidence
    definitely_count = sum(1 for f in findings if f['confidence'] == 'definitely')
    likely_count = sum(1 for f in findings if f['confidence'] == 'likely')
    possible_count = sum(1 for f in findings if f['confidence'] == 'possible')
    
    # Insert scan
    cursor.execute("""
        INSERT INTO scans (project_name, timestamp, total_files, total_findings,
                          definitely_count, likely_count, possible_count, passed, findings_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Test Fixtures (Leaky)",
        datetime.now().isoformat(),
        len(list(leaky_dir.glob("*.py"))),
        len(findings),
        definitely_count,
        likely_count,
        possible_count,
        False,
        json.dumps(findings)
    ))
    
    conn.commit()
    print(f"✅ Seeded database with {len(findings)} findings from test fixtures")
    
    # Also scan clean fixtures for comparison
    clean_dir = Path("tests/fixtures/clean")
    clean_findings = []
    
    for py_file in clean_dir.glob("*.py"):
        try:
            file_findings = analyze_file(py_file)
            for finding in file_findings:
                clean_findings.append({
                    'file': str(finding.file_path),
                    'line': finding.acquisition_line,
                    'resource_type': finding.resource_type,
                    'resource_expr': finding.resource_expr,
                    'confidence': finding.confidence.value,
                    'explanation': finding.explanation
                })
        except Exception as e:
            pass
    
    cursor.execute("""
        INSERT INTO scans (project_name, timestamp, total_files, total_findings,
                          definitely_count, likely_count, possible_count, passed, findings_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        "Test Fixtures (Clean)",
        datetime.now().isoformat(),
        len(list(clean_dir.glob("*.py"))),
        len(clean_findings),
        0,
        0,
        len(clean_findings),
        len(clean_findings) == 0,
        json.dumps(clean_findings)
    ))
    
    conn.commit()
    conn.close()
    
    print(f"✅ Also added clean fixtures scan ({len(clean_findings)} findings)")
    print("\n🚀 Dashboard is ready! Run: python dashboard/main.py")

if __name__ == "__main__":
    seed_database()
