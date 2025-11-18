# IBE Email System - Web Interface Launcher
# This script starts both the SMTP debug server and web interface

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "   IBE Email System - Web Interface Launcher" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

# Set PYTHONPATH
$env:PYTHONPATH = "d:\OneDrive\Documents\cypto_proj"

Write-Host "Starting servers..." -ForegroundColor Yellow
Write-Host ""

# Start SMTP debug server in background
Write-Host "[1/2] Starting SMTP Debug Server on port 1025..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PWD'; python scripts\debug_smtp_server.py --port 1025"
Start-Sleep -Seconds 2

# Start web interface
Write-Host "[2/2] Starting Web Interface on port 5001..." -ForegroundColor Green
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  Web Interface will open at: http://127.0.0.1:5001" -ForegroundColor Green
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "INSTRUCTIONS:" -ForegroundColor Yellow
Write-Host "  1. A browser window should open automatically" -ForegroundColor Gray
Write-Host "  2. If not, manually open: http://127.0.0.1:5001" -ForegroundColor Gray
Write-Host "  3. Check the SMTP debug server window for OTP codes" -ForegroundColor Gray
Write-Host "  4. Press Ctrl+C in this window to stop the web server" -ForegroundColor Gray
Write-Host ""
Write-Host "================================================================" -ForegroundColor Cyan
Write-Host ""

Start-Sleep -Seconds 2

# Open browser
Start-Process "http://127.0.0.1:5001"

# Run web interface
python web_interface.py
