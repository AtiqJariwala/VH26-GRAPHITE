# LeakGuard CLI wrapper script for PowerShell
# Usage: .\leakguard.ps1 scan <path>

python -m leakguard.cli $args
exit $LASTEXITCODE
