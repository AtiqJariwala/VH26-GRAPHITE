# LeakGuard Demo Script
# This demonstrates the enhanced visual output and CI build blocking

Write-Host "`n===========================================`n" -ForegroundColor Cyan
Write-Host "   LEAKGUARD PROFESSIONAL DEMO" -ForegroundColor Cyan
Write-Host "`n===========================================`n" -ForegroundColor Cyan

Write-Host "`n[1/4] Scanning a LEAKY file (will detect and block)...`n" -ForegroundColor Yellow
python -m leakguard.cli scan tests\fixtures\leaky\01_simple_file_leak.py
Write-Host "`n✓ See the beautiful colored output above!`n" -ForegroundColor Green

Start-Sleep -Seconds 2

Write-Host "`n[2/4] Scanning a CLEAN file (will pass)...`n" -ForegroundColor Yellow
python -m leakguard.cli scan tests\fixtures\clean\01_with_statement.py  
Write-Host "`n✓ No leaks found - build would pass!`n" -ForegroundColor Green

Start-Sleep -Seconds 2

Write-Host "`n[3/4] Scanning ALL leaky fixtures (comprehensive test)...`n" -ForegroundColor Yellow
python -m leakguard.cli scan tests\fixtures\leaky\

Start-Sleep -Seconds 2

Write-Host "`n[4/4] Scanning ALL clean fixtures (should pass)...`n" -ForegroundColor Yellow
python -m leakguard.cli scan tests\fixtures\clean\

Write-Host "`n===========================================`n" -ForegroundColor Cyan
Write-Host "   DEMO COMPLETE!" -ForegroundColor Cyan
Write-Host "`n===========================================`n" -ForegroundColor Cyan
Write-Host "This is what runs in CI/CD pipelines automatically!" -ForegroundColor Green
Write-Host "Any leaked resources = Build BLOCKED ❌`n" -ForegroundColor Red
