# LeakGuard - Production Setup Guide

**Complete setup instructions for the final production-ready version**

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Installation](#installation)
3. [Dashboard Setup](#dashboard-setup)
4. [CI/CD Configuration](#cicd-configuration)
5. [Configuration File](#configuration-file)
6. [Usage Examples](#usage-examples)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

### 1. Install LeakGuard

```bash
# Clone the repository
git clone <repository-url>
cd VH26-GRAPHITE

# Install in editable mode
pip install -e .

# Verify installation
leakguard --help
```

### 2. Run Your First Scan

```bash
# Scan a single file
leakguard scan path/to/file.py

# Scan entire directory
leakguard scan .

# Scan with custom threshold
leakguard scan . --fail-on=definitely
```

### 3. Start the Dashboard

```bash
# Option 1: Use the provided script
./start_dashboard.ps1

# Option 2: Run directly
python dashboard/main.py

# Dashboard will be available at http://127.0.0.1:8000
```

---

## Installation

### Requirements

- Python 3.10 or higher
- pip

### Core Installation

```bash
# Basic installation (CLI only)
pip install -e .

# With dashboard support
pip install -e .
pip install fastapi uvicorn jinja2

# With rich terminal output (optional)
pip install rich
```

### Verify Installation

```bash
# Check CLI works
leakguard scan tests/fixtures/leaky/01_simple_file_leak.py

# Should output findings and exit with code 1

# Check clean code
leakguard scan tests/fixtures/clean/01_with_statement.py

# Should output "No leaks detected" and exit with code 0
```

---

## Dashboard Setup

### Starting the Dashboard

```bash
# Method 1: PowerShell script (recommended)
.\start_dashboard.ps1

# Method 2: Direct Python
python dashboard/main.py

# Method 3: Custom port
python -c "from dashboard.main import *; import uvicorn; uvicorn.run(app, host='127.0.0.1', port=8080)"
```

### Dashboard Features

#### 1. **Automatic Scanning**
- Click "New Scan" button
- Enter project name and directory path
- Click "Run Scan" - results appear automatically

#### 2. **Findings Table**
- Sticky header stays visible while scrolling
- Click any row to expand detailed information
- Real-time filters:
  - Confidence level dropdown
  - Resource type selection
  - Path search (instant)

#### 3. **Settings**
- Click "Settings" button
- Configure fail-on threshold
- Add ignore patterns (glob format)
- Define safe-transfer functions
- Settings saved to SQLite database

#### 4. **Export Results**
- Click "Export JSON" button
- Downloads current scan results as JSON file
- Includes all findings with metadata

#### 5. **Scan History**
- Left sidebar shows last 10 scans
- Click any scan to load it
- Color-coded: green=pass, red=fail

### Seeding Demo Data

```bash
# Populate database with test fixture scans
python dashboard/seed.py

# This creates sample scans you can explore immediately
```

---

## CI/CD Configuration

### Pre-Commit Hook (Blocks Commits with Leaks)

#### 1. Install pre-commit

```bash
pip install pre-commit
```

#### 2. Install the hook

```bash
pre-commit install
```

#### 3. Configuration

The `.pre-commit-config.yaml` is already configured:

```yaml
repos:
  - repo: local
    hooks:
      - id: leakguard
        name: LeakGuard Resource Leak Detector
        entry: python -m leakguard.cli scan
        language: system
        types: [python]
        pass_filenames: false
        args: ["."]
        files: \.py$
```

#### 4. Test It

```bash
# This will be BLOCKED by the hook
echo "f = open('test.txt')" > temp_leak.py
git add temp_leak.py
git commit -m "test"

# Expected: commit is BLOCKED, exit code 1

# This will PASS
echo "with open('test.txt') as f: pass" > temp_clean.py
git add temp_clean.py
git commit -m "test"

# Expected: commit succeeds, exit code 0
```

### GitHub Action (Blocks PRs with Leaks)

The `.github/workflows/leakguard.yml` is configured to **FAIL the build** when leaks are found.

#### How It Works:

1. **On push/PR** → GitHub runs the workflow
2. **Installs LeakGuard** → `pip install -e .`
3. **Runs scan** → `leakguard scan . --fail-on=likely`
4. **Checks exit code** → Non-zero = FAIL and ABORT

#### Enable Branch Protection:

1. Go to repository **Settings** → **Branches**
2. Add branch protection rule for `main`
3. Enable **"Require status checks to pass before merging"**
4. Select **"leakguard"** as required check
5. Save

Now PRs with leaks cannot be merged!

#### Test It:

```bash
# Create a new branch with a leak
git checkout -b test-leak
echo "f = open('leak.txt')" > leak_test.py
git add leak_test.py
git commit -m "Add leak"
git push origin test-leak

# Go to GitHub and create PR
# Expected: GitHub Action fails, PR cannot be merged
```

---

## Configuration File

### Option 1: `.leakguard.toml`

Create `.leakguard.toml` in your project root:

```toml
# Confidence level at which to fail builds
# Options: "definitely", "likely", "possible"
fail-on = "likely"

# Patterns to ignore (glob patterns)
ignore-patterns = [
    "tests/*",
    "build/*",
    "*.egg-info/*",
    "__pycache__/*"
]

# Functions known to take ownership of resources
safe-transfer-functions = [
    "contextlib.closing",
    "weakref.finalize"
]
```

### Option 2: `pyproject.toml`

Add to your existing `pyproject.toml`:

```toml
[tool.leakguard]
fail-on = "likely"
ignore-patterns = ["tests/*", "build/*"]
safe-transfer-functions = ["contextlib.closing"]
```

### Configuration Priority

1. **CLI arguments** (highest priority)
2. **`.leakguard.toml`** in project root
3. **`pyproject.toml`** `[tool.leakguard]` section
4. **Default values** (fail-on=likely)

### Example: Override Config

```bash
# Config file says fail-on=likely
# Override with CLI arg:
leakguard scan . --fail-on=definitely

# CLI arg wins
```

---

## Usage Examples

### Basic Scanning

```bash
# Scan single file
leakguard scan demo_leak.py

# Scan directory
leakguard scan test_samples/

# Scan current directory
leakguard scan .
```

### With Confidence Thresholds

```bash
# Only fail on confirmed leaks (least strict)
leakguard scan . --fail-on=definitely

# Fail on likely leaks (recommended)
leakguard scan . --fail-on=likely

# Fail on any potential leak (most strict)
leakguard scan . --fail-on=possible
```

### Integration Examples

#### In Makefile

```makefile
.PHONY: test
test:
	pytest
	leakguard scan src/ --fail-on=likely
```

#### In CI Script

```bash
#!/bin/bash
set -e

echo "Running tests..."
pytest

echo "Checking for resource leaks..."
leakguard scan . --fail-on=likely

echo "All checks passed!"
```

#### In Docker Build

```dockerfile
FROM python:3.10

COPY . /app
WORKDIR /app

RUN pip install -e .
RUN leakguard scan . --fail-on=likely

# Build fails if leaks found
```

---

## Troubleshooting

### CLI Issues

**Problem:** `leakguard: command not found`

**Solution:**
```bash
# Ensure installed
pip install -e .

# Or use module form
python -m leakguard.cli scan file.py
```

**Problem:** No colors in output

**Solution:**
```bash
# Install rich (optional)
pip install rich

# Without rich, you get plain text output (still works)
```

### Dashboard Issues

**Problem:** `Internal Server Error` when loading dashboard

**Solution:**
```bash
# Restart the server
python dashboard/main.py

# Dashboard auto-finds available port (8000-8010)
```

**Problem:** "No scans yet" in sidebar

**Solution:**
```bash
# Seed demo data
python dashboard/seed.py

# Or run a new scan via CLI
leakguard scan test_samples/

# Then refresh dashboard
```

**Problem:** Scan button doesn't work

**Solution:**
- The scan path must be valid (absolute or relative to workspace root)
- Try using `tests/fixtures/leaky` as a test path
- Check browser console for errors (F12)

### Pre-Commit Hook Issues

**Problem:** Hook doesn't run

**Solution:**
```bash
# Reinstall hook
pre-commit uninstall
pre-commit install

# Test manually
pre-commit run leakguard --all-files
```

**Problem:** Hook runs but doesn't block

**Solution:**
```bash
# Verify CLI exits with code 1 on leaks
leakguard scan tests/fixtures/leaky/
echo $LASTEXITCODE  # Should be 1

# If not 1, reinstall LeakGuard
pip uninstall leakguard
pip install -e .
```

### GitHub Action Issues

**Problem:** Action passes even with leaks

**Solution:**
- Check `.github/workflows/leakguard.yml` has explicit exit code check
- Verify the scan step doesn't have `continue-on-error: true`
- Look at action logs to see actual exit code

**Problem:** Action fails with "command not found"

**Solution:**
```yaml
# In workflow, ensure installation step runs
- name: Install LeakGuard
  run: |
    pip install -e .
```

---

## Exit Codes

LeakGuard uses standard Unix exit codes:

- **0** - Success (no leaks found)
- **1** - Failure (leaks found at or above threshold)

This makes it CI/CD-friendly:

```bash
leakguard scan .
if [ $? -eq 0 ]; then
    echo "✅ No leaks detected"
else
    echo "❌ Leaks found, build failed"
    exit 1
fi
```

---

## Key Files Reference

- **`.pre-commit-config.yaml`** - Pre-commit hook configuration
- **`.github/workflows/leakguard.yml`** - GitHub Action workflow
- **`.leakguard.toml`** - Optional project configuration
- **`dashboard/main.py`** - Dashboard backend
- **`dashboard/templates/index.html`** - Dashboard frontend
- **`leakguard/analyzer.py`** - Core AST analyzer
- **`leakguard/cli.py`** - Command-line interface
- **`leakguard/config.py`** - Configuration loader

---

## What's Working (Production-Ready)

✅ **AST Analyzer**
- Early return detection
- Try/except/finally path tracking
- Context manager recognition
- Reassignment detection
- Confidence levels (definitely/likely/possible)

✅ **CLI**
- Proper exit codes (0=clean, 1=leaks)
- Configuration file support
- Rich terminal output (optional)
- Recursive directory scanning

✅ **Pre-Commit Hook**
- Blocks commits with leaks
- Configurable threshold
- Scans full repository

✅ **GitHub Action**
- Fails build on leaks
- Clear output
- Works with branch protection

✅ **Dashboard**
- Automatic scan trigger
- Real-time filters
- Expandable finding details
- Settings page
- JSON export
- Scan history
- Professional UI

---

## Support & Documentation

- **Limitations:** See `docs/limitations.md` or dashboard "Limitations" page
- **Contributing:** See `CONTRIBUTING.md`
- **Examples:** Check `test_samples/` directory

---

**This is the FINAL production-ready version. No TODOs, no compromises, everything works.**
