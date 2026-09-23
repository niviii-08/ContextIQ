$ErrorActionPreference = "Stop"
Write-Host "Starting ContextIQ Services..." -ForegroundColor Cyan

$basePath = Get-Location

# 1. Core Backend
Write-Host "Starting Core Backend (8000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8000" -WorkingDirectory $basePath

# 2. Data Engine
Write-Host "Starting Data Engine (8001)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd data-engine; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; python scripts/init_db.py; uvicorn app.main:app --reload --port 8001" -WorkingDirectory $basePath

# 3. Forgetting ML
Write-Host "Starting Forgetting ML (8002)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd forgetting-ml; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8002" -WorkingDirectory $basePath

# 4. Context Engine
Write-Host "Starting Context Engine (8003)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd context-engine; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; uvicorn app.main:app --reload --port 8003" -WorkingDirectory $basePath

# 5. Intelligence Service
Write-Host "Starting Intelligence Service (8004)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd intelligence; if (!(Test-Path .venv)) { python -m venv .venv }; .\.venv\Scripts\activate; pip install -r requirements.txt; if (!(Test-Path .env)) { Copy-Item .env.example .env }; uvicorn app.main:app --reload --port 8004" -WorkingDirectory $basePath

# 6. Frontend
Write-Host "Starting Frontend (3000)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm install; if (!(Test-Path .env.local)) { Copy-Item .env.example .env.local }; npm run dev" -WorkingDirectory $basePath

Write-Host "All services have been launched in separate windows!" -ForegroundColor Green
Write-Host "Wait a minute for dependencies to install (if this is the first run) and servers to spin up." -ForegroundColor Green
Write-Host "Frontend will be available at: http://localhost:3000" -ForegroundColor Cyan
