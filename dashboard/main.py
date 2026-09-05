"""
LeakGuard Dashboard Backend

FastAPI server that wraps the existing LeakGuard analyzer
and provides a clean web interface for viewing results.
"""

from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.requests import Request
from pathlib import Path
from typing import List, Optional
import json
import sqlite3
from datetime import datetime
import sys

# Import the existing LeakGuard analyzer
sys.path.insert(0, str(Path(__file__).parent.parent))
from leakguard.analyzer import analyze_file
from leakguard.confidence import Confidence

app = FastAPI(title="LeakGuard Dashboard")
templates = Jinja2Templates(directory="dashboard/templates")

# Database connection
DB_PATH = Path("dashboard/db/scans.db")

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database schema"""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Scans table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            total_files INTEGER,
            total_findings INTEGER,
            definitely_count INTEGER,
            likely_count INTEGER,
            possible_count INTEGER,
            passed BOOLEAN,
            findings_json TEXT
        )
    """)
    
    # Settings table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)
    
    # Default settings
    cursor.execute("INSERT OR IGNORE INTO settings VALUES ('fail_on', 'likely')")
    cursor.execute("INSERT OR IGNORE INTO settings VALUES ('ignore_patterns', '[]')")
    
    conn.commit()
    conn.close()

# Initialize on startup
init_db()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/scans")
async def list_scans():
    """Get list of all scans"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, project_name, timestamp, total_files, total_findings,
               definitely_count, likely_count, possible_count, passed
        FROM scans ORDER BY timestamp DESC
    """)
    scans = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return {"scans": scans}


@app.get("/api/scans/{scan_id}")
async def get_scan(scan_id: int):
    """Get detailed scan results"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scans WHERE id = ?", (scan_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    scan = dict(row)
    scan['findings'] = json.loads(scan['findings_json'])
    del scan['findings_json']
    return scan


@app.post("/api/scan")
async def run_scan(project_name: str, file_paths: List[str]):
    """
    Run LeakGuard analysis on provided files
    
    This calls the existing analyzer.py from the leakguard package
    """
    findings = []
    
    for file_path in file_paths:
        try:
            path = Path(file_path)
            if not path.exists():
                continue
                
            file_findings = analyze_file(path)
            
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
            # Log but continue with other files
            print(f"Error analyzing {file_path}: {e}")
    
    # Count by confidence
    definitely_count = sum(1 for f in findings if f['confidence'] == 'definitely')
    likely_count = sum(1 for f in findings if f['confidence'] == 'likely')
    possible_count = sum(1 for f in findings if f['confidence'] == 'possible')
    
    # Determine pass/fail based on settings
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'fail_on'")
    fail_on = cursor.fetchone()[0]
    
    passed = True
    if fail_on == 'definitely' and definitely_count > 0:
        passed = False
    elif fail_on == 'likely' and (definitely_count > 0 or likely_count > 0):
        passed = False
    elif fail_on == 'possible' and len(findings) > 0:
        passed = False
    
    # Store in database
    cursor.execute("""
        INSERT INTO scans (project_name, timestamp, total_files, total_findings,
                          definitely_count, likely_count, possible_count, passed, findings_json)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        project_name,
        datetime.now().isoformat(),
        len(file_paths),
        len(findings),
        definitely_count,
        likely_count,
        possible_count,
        passed,
        json.dumps(findings)
    ))
    
    scan_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        'scan_id': scan_id,
        'total_findings': len(findings),
        'definitely_count': definitely_count,
        'likely_count': likely_count,
        'possible_count': possible_count,
        'passed': passed,
        'findings': findings
    }


@app.get("/api/settings")
async def get_settings():
    """Get current settings"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT key, value FROM settings")
    settings = {row['key']: row['value'] for row in cursor.fetchall()}
    conn.close()
    return settings


@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update settings"""
    conn = get_db()
    cursor = conn.cursor()
    
    for key, value in settings.items():
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)
        """, (key, value))
    
    conn.commit()
    conn.close()
    return {"status": "success"}


if __name__ == "__main__":
    import uvicorn
    import socket
    
    # Try ports 8000-8010 until we find one available
    port = 8000
    for attempt_port in range(8000, 8011):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', attempt_port))
            sock.close()
            port = attempt_port
            break
        except OSError:
            continue
    
    print(f"\n🚀 LeakGuard Dashboard starting on http://127.0.0.1:{port}\n")
    uvicorn.run(app, host="127.0.0.1", port=port)
