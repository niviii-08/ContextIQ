$ErrorActionPreference = "Stop"
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "  Starting ContextIQ & Micro-Delay Analytics (Full Stack) " -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$basePath = if ($PSScriptRoot) { $PSScriptRoot } else { Get-Location }

# 1. Core Backend (Port 8000)
Write-Host "[1/6] Launching Core Backend API (Port 8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$basePath\backend'; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; uvicorn app.main:app --reload --port 8000"

# 2. Data Engine (Port 8001)
Write-Host "[2/6] Launching Data & Micro-Delay Engine (Port 8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$basePath\data-engine'; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; python scripts/populate_sqlite_full.py; uvicorn app.main:app --reload --port 8001"

# 3. Forgetting ML (Port 8002)
Write-Host "[3/6] Launching Forgetting Prediction ML Engine (Port 8002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$basePath\forgetting-ml'; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; uvicorn app.main:app --reload --port 8002"

# 4. Context Engine (Port 8003)
Write-Host "[4/6] Launching Context Mining & Switch Engine (Port 8003)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$basePath\context-engine'; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8003"

# 5. Intelligence Service (Port 8004)
Write-Host "[5/6] Launching AI Intelligence & Explanation Service (Port 8004)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$basePath\intelligence'; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; uvicorn app.main:app --reload --port 8004"

# 6. Next.js Frontend (Port 3001)
Write-Host "[6/6] Launching Next.js 16 Dashboard UI (Port 3001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$basePath\frontend'; if (!(Test-Path node_modules)) { npm install }; if (!(Test-Path .env.local)) { Copy-Item .env.example .env.local }; npm run dev"

Write-Host "----------------------------------------------------------" -ForegroundColor Green
Write-Host "All 6 ContextIQ services launched in dedicated terminals!" -ForegroundColor Green
Write-Host "Services will be active at:" -ForegroundColor Cyan
Write-Host "  - Frontend UI:         http://localhost:3001" -ForegroundColor White
Write-Host "  - Core API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Data Engine Docs:    http://localhost:8001/docs" -ForegroundColor White
Write-Host "  - Forgetting ML Docs:  http://localhost:8002/docs" -ForegroundColor White
Write-Host "  - Context Engine Docs: http://localhost:8003/docs" -ForegroundColor White
Write-Host "  - Intelligence Docs:   http://localhost:8004/docs" -ForegroundColor White
Write-Host "----------------------------------------------------------" -ForegroundColor Green
