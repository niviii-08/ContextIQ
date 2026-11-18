Write-Host "========================================================" -ForegroundColor Cyan
Write-Host "         Starting ContextIQ Microservices Suite         " -ForegroundColor Cyan
Write-Host "========================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

# 1. Backend API (Port 8000)
Write-Host "[1/3] Starting Backend API on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\backend'; & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --port 8000 --host 0.0.0.0 --reload"

Start-Sleep -Seconds 2

# 2. Data Engine (Port 8001)
Write-Host "[2/3] Starting Data Engine on port 8001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\data-engine'; & '.\.venv\Scripts\python.exe' -m uvicorn app.main:app --port 8001 --host 0.0.0.0"

Start-Sleep -Seconds 2

# 3. Frontend (Port 3001)
Write-Host "[3/3] Starting Frontend Next.js on port 3001..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$root\frontend'; npm run dev"

Write-Host ""
Write-Host "========================================================" -ForegroundColor Green
Write-Host " All services launched in separate PowerShell windows!   " -ForegroundColor Green
Write-Host " - Frontend Web UI:    http://localhost:3001           " -ForegroundColor Green
Write-Host " - Backend API Docs:   http://localhost:8000/docs      " -ForegroundColor Green
Write-Host " - Data Engine Docs:   http://localhost:8001/docs      " -ForegroundColor Green
Write-Host " - PostgreSQL DB:      localhost:5433/dataproject       " -ForegroundColor Green
Write-Host "========================================================" -ForegroundColor Green
