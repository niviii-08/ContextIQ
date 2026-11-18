@echo off
title ContextIQ Launcher
echo ========================================================
echo          Starting ContextIQ Microservices Suite
echo ========================================================
echo.

echo [1/3] Starting Backend API (Port 8000)...
start "ContextIQ - Backend API (Port 8000)" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8000 --host 0.0.0.0 --reload"

timeout /t 2 /nobreak >nul

echo [2/3] Starting Data Engine (Port 8001)...
start "ContextIQ - Data Engine (Port 8001)" cmd /k "cd /d "%~dp0data-engine" && .venv\Scripts\python.exe -m uvicorn app.main:app --port 8001 --host 0.0.0.0"

timeout /t 2 /nobreak >nul

echo [3/3] Starting Frontend (Port 3001)...
start "ContextIQ - Frontend (Port 3001)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ========================================================
echo  All services launched in separate windows!
echo  - Frontend Web UI:    http://localhost:3001
echo  - Backend API Docs:   http://localhost:8000/docs
echo  - Data Engine Docs:   http://localhost:8001/docs
echo  - PostgreSQL DB:      localhost:5433/dataproject
echo ========================================================
pause
