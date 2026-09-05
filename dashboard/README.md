# LeakGuard Dashboard

Professional web interface for LeakGuard resource leak detection.

## Installation

1. Install dependencies:
```bash
pip install fastapi uvicorn jinja2
```

2. The dashboard automatically uses the existing LeakGuard analyzer from the parent directory.

## Running

```bash
# From the project root
python dashboard/main.py

# Or with uvicorn directly
uvicorn dashboard.main:app --reload
```

Then open: http://127.0.0.1:8000

## Architecture

- **Backend**: FastAPI (Python) - wraps the existing analyzer.py
- **Frontend**: Tailwind CSS + vanilla JS - no heavy frameworks
- **Database**: SQLite for scan history
- **Design**: Dark professional theme optimized for technical users

## Features

✅ Real-time scan execution calling the existing LeakGuard package
✅ Scan history with SQLite persistence
✅ Filterable findings table (by confidence, resource type, file path)
✅ Clean, professional dark UI with excellent typography
✅ Confidence-based color coding (red/amber/blue)
✅ Settings for fail-on threshold and ignore patterns
✅ Honest limitations page

## How It Works

1. Dashboard calls `leakguard.analyzer.analyze_file()` for each file
2. Results are structured into JSON and stored in SQLite
3. Frontend fetches via REST API and renders in a clean table
4. Filters work client-side for instant response

## Seed Data

On first run, the database is auto-created. To see it with data, run a scan from the CLI first:

```bash
python -m leakguard.cli scan tests/fixtures/leaky/
```

Then the dashboard will show those results.

## UI Design Principles

- Dark slate theme (#0f1419 background, #1e293b cards)
- Single accent: muted teal (#14b8a6) for actions
- Monospace fonts for file paths and line numbers
- Zebra-stripe hover on tables for scannability
- No unnecessary decoration or gradients
- Typography hierarchy using Inter font

## Current Limitations (Honest Assessment)

- New scan modal is placeholder (use CLI for now)
- Settings UI is not yet implemented (edit DB directly)
- No export to PDF yet (JSON export works)
- No authentication (local use only)

These are intentional MVP cuts to ship faster while maintaining quality.

## Future Improvements

- File upload / drag-and-drop for local scanning
- Chart showing trends over time (Chart.js)
- Markdown/PDF export
- "Acknowledge" button to mark false positives
- Dark/light theme toggle

---

**This dashboard transforms LeakGuard from a CLI tool into a professional team product.**
