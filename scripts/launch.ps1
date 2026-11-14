<# 
.SYNOPSIS
    Launch Global Airdrop Hunter in browser app mode (fallback for Electron)

.DESCRIPTION
    Starts the FastAPI backend and opens the frontend in Microsoft Edge app mode
    (chromeless window) for a native app-like experience without Electron.

.NOTES
    Run from project root: E:\Global Airdrop Hunter
    Requires: Microsoft Edge (installed by default on Windows 10/11)
#>

param(
    [switch]$DevTools,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent
$ProjectRoot = Resolve-Path $ProjectRoot

Write-Host "=== Global Airdrop Hunter - Browser App Mode Launcher ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

$venvPath = Join-Path $ProjectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$backendDir = Join-Path $ProjectRoot "backend"
$dbPath = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\app.db"
$frontendPath = Join-Path $ProjectRoot "frontend\index.html"

if (-not (Test-Path $pythonExe)) {
    Write-Host "ERROR: Virtual environment not found at $venvPath" -ForegroundColor Red
    Write-Host "Run .\scripts\setup.ps1 first" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $dbPath)) {
    Write-Host "WARNING: Database not found at $dbPath" -ForegroundColor Yellow
    Write-Host "Run .\scripts\setup.ps1 to initialize" -ForegroundColor Yellow
}

$env:PYTHONPATH = $backendDir
$env:DATABASE_PATH = $dbPath
$env:BACKEND_PORT = $Port.ToString()
$env:APP_DATA_DIR = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter"

$backendProcess = $null
$edgeProcess = $null

function Stop-Processes {
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    if ($edgeProcess) {
        Stop-Process -Id $edgeProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Frontend closed" -ForegroundColor Gray
    }
    if ($backendProcess) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Backend stopped" -ForegroundColor Gray
    }
}

function Check-BackendHealth {
    param($port, $token, $maxAttempts = 30)
    Write-Host "  Waiting for backend health check..." -NoNewline -ForegroundColor Gray
    for ($i = 1; $i -le $maxAttempts; $i++) {
        try {
            $response = Invoke-RestMethod -Uri "http://127.0.0.1:$port/api/v1/health" `
                -Headers @{ "X-Local-API-Token" = $token } -Method Get -TimeoutSec 2 -ErrorAction Stop
            if ($response.status -eq "healthy") {
                Write-Host " OK" -ForegroundColor Green
                return $true
            }
        } catch {
            Write-Host "." -NoNewline -ForegroundColor Gray
            Start-Sleep -Milliseconds 500
        }
    }
    Write-Host " FAILED" -ForegroundColor Red
    return $false
}

try {
    Write-Host "`nStarting FastAPI backend on http://127.0.0.1:$Port..." -ForegroundColor Yellow
    $backendProcess = Start-Process -FilePath $pythonExe `
        -ArgumentList "-m", "uvicorn", "backend.main:app", "--host", "127.0.0.1", "--port", $Port.ToString() `
        -WorkingDirectory $ProjectRoot `
        -PassThru
    Write-Host "  Backend PID: $($backendProcess.Id)" -ForegroundColor Gray

    $token = -join ((1..32) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })
    $env:LOCAL_API_TOKEN = $token

    if (-not (Check-BackendHealth -port $Port -token $token)) {
        throw "Backend health check failed"
    }

    Write-Host "`nOpening frontend in Microsoft Edge app mode..." -ForegroundColor Yellow
    $launchUrl = "http://127.0.0.1:$Port/api/v1/launch"
    $userDataDir = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\EdgeProfile"
    if (-not (Test-Path $userDataDir)) { New-Item -ItemType Directory -Path $userDataDir -Force | Out-Null }
    $edgeArgs = "--app=$launchUrl", "--user-data-dir=$userDataDir", "--no-first-run", "--no-default-browser-check"
    if ($DevTools) { $edgeArgs += " --auto-open-devtools-for-tabs" }
    
    $edgeProcess = Start-Process -FilePath "msedge.exe" `
        -ArgumentList $edgeArgs `
        -PassThru
    Write-Host "  Edge PID: $($edgeProcess.Id)" -ForegroundColor Gray

    Write-Host "`nApplication running. Close the Edge window to exit." -ForegroundColor Green
    Write-Host "  (Keep this console window open)" -ForegroundColor Gray
    $edgeProcess.WaitForExit()
    Stop-Processes
}
catch {
    Write-Host "`nERROR: $_" -ForegroundColor Red
    Stop-Processes
    exit 1
}
finally {
    Stop-Processes
}