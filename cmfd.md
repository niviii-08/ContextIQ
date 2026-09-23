# Running ContextIQ on Windows (Without Docker)

Since you are running the project manually on Windows without Docker, you will need to start each of the 6 services independently. 

I have outlined the manual terminal commands below, but **I highly recommend using the automated PowerShell script (`start_windows.ps1`)** that I also created for you to launch everything with one click!

## Option 1: The Automated Way (1-Click Start)
I created a PowerShell script that will automatically open 6 new windows and start every service for you.

To use it, just run this in your root `contextiq-complete` folder:
```powershell
.\start_windows.ps1
```
*(If you get a permissions error, run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` first).*

---

## Option 2: The Manual Way (6 Terminals)
If you prefer to start them manually, open **6 separate PowerShell windows** in the `contextiq-complete` directory. Run one of these blocks in each window. 

*(Note: The first time you run these, they will install their dependencies. Subsequent runs will be much faster).*

### 1. Core Backend (Port 8000)
```powershell
cd backend
.\.venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

### 2. Data Engine (Port 8001)
```powershell
cd data-engine
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
python scripts/init_db.py
uvicorn app.main:app --reload --port 8001
```

### 3. Forgetting ML (Port 8002)
```powershell
cd forgetting-ml
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8002
```

### 4. Context Engine (Port 8003)
```powershell
cd context-engine
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8003
```

### 5. Intelligence Service (Port 8004)
```powershell
cd intelligence
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
Copy-Item .env.example .env
uvicorn app.main:app --reload --port 8004
```

### 6. Frontend (Port 3000)
```powershell
cd frontend
npm install
Copy-Item .env.example .env.local
npm run dev
```
