# Quick Start Script for LeakGuard Dashboard

Write-Host "`n=== LeakGuard Dashboard Setup ===`n" -ForegroundColor Cyan

# Step 1: Install dependencies
Write-Host "[1/3] Installing Python dependencies..." -ForegroundColor Yellow
pip install -q fastapi uvicorn jinja2

# Step 2: Seed database
Write-Host "[2/3] Seeding database with test data..." -ForegroundColor Yellow
python dashboard/seed.py

# Step 3: Start server
Write-Host "[3/3] Starting dashboard server..." -ForegroundColor Yellow
Write-Host "`n✅ Dashboard will open at: http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Press Ctrl+C to stop`n" -ForegroundColor Gray

python dashboard/main.py
