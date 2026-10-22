Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "   ContextIQ System Health Verification   " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# 1. Port checks
Write-Host "`n[1] Checking Active Network Ports..." -ForegroundColor Yellow
$ports = Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -in 3001, 8000, 8001, 5433 } | Select-Object LocalPort, OwningProcess | Sort-Object LocalPort -Unique
$ports | Format-Table -AutoSize

$activePortList = $ports.LocalPort
foreach ($p in @(3001, 8000, 8001, 5433)) {
    if ($activePortList -contains $p) {
        Write-Host "  [OK] Port $p is actively listening." -ForegroundColor Green
    } else {
        Write-Host "  [WARN] Port $p is NOT listening." -ForegroundColor Red
    }
}

# 2. Core Backend API Health
Write-Host "`n[2] Checking Core Backend API (:8000)..." -ForegroundColor Yellow
try {
    $res = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/health" -Method Get
    Write-Host "  [OK] /api/v1/health returned: $($res | ConvertTo-Json -Compress)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Failed to reach /api/v1/health: $_" -ForegroundColor Red
}

# 3. Data Engine API Health
Write-Host "`n[3] Checking Data Engine API (:8001)..." -ForegroundColor Yellow
try {
    $res = Invoke-WebRequest -Uri "http://localhost:8001/docs" -UseBasicParsing
    Write-Host "  [OK] Data Engine Docs returned HTTP $($res.StatusCode)" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Failed to reach Data Engine: $_" -ForegroundColor Red
}

# 4. Frontend Routes Check
Write-Host "`n[4] Checking Frontend Dashboard Pages (:3001)..." -ForegroundColor Yellow
$routes = @(
    @{ Path = "/"; Label = "Dashboard Overview" },
    @{ Path = "/context"; Label = "Context & Micro-Delays" },
    @{ Path = "/predictions"; Label = "Forgetting Risk Predictions" },
    @{ Path = "/insights"; Label = "Behavioral Insights" },
    @{ Path = "/recommendations"; Label = "Contextual Recommendations" },
    @{ Path = "/tasks"; Label = "Tasks & Interruption Logger" }
)

foreach ($r in $routes) {
    try {
        $res = Invoke-WebRequest -Uri ("http://localhost:3001" + $r.Path) -UseBasicParsing
        if ($res.StatusCode -eq 200) {
            Write-Host "  [OK] $($r.Label) ($($r.Path)) -> HTTP 200 OK" -ForegroundColor Green
        } else {
            Write-Host "  [WARN] $($r.Label) ($($r.Path)) -> HTTP $($res.StatusCode)" -ForegroundColor Yellow
        }
    } catch {
        Write-Host "  [FAIL] $($r.Label) ($($r.Path)) -> Connection Failed: $_" -ForegroundColor Red
    }
}

Write-Host "`n==========================================" -ForegroundColor Cyan
Write-Host "       Verification Audit Completed       " -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
