<# 
.SYNOPSIS
    Start Global Airdrop Hunter application

.DESCRIPTION
    Starts the FastAPI backend and Electron frontend.
    The backend runs on http://127.0.0.1:8000
    The Electron app connects to the backend via IPC.

.NOTES
    Run from project root: E:\Global Airdrop Hunter
#>

param(
    [switch]$Dev,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [int]$Port = 8000
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent
$ProjectRoot = Resolve-Path $ProjectRoot

Write-Host "=== Global Airdrop Hunter - Starting Application ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

$venvPath = Join-Path $ProjectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$backendDir = Join-Path $ProjectRoot "backend"
$dbPath = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\app.db"

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
$electronProcess = $null

function Stop-Processes {
    Write-Host "`nShutting down..." -ForegroundColor Yellow
    if ($backendProcess) {
        Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Backend stopped" -ForegroundColor Gray
    }
    if ($electronProcess) {
        Stop-Process -Id $electronProcess.Id -Force -ErrorAction SilentlyContinue
        Write-Host "  Frontend stopped" -ForegroundColor Gray
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
    if (-not $FrontendOnly) {
        Write-Host "`nStarting FastAPI backend on http://127.0.0.1:$Port..." -ForegroundColor Yellow
        $backendProcess = Start-Process -FilePath $pythonExe `
            -ArgumentList "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", $Port.ToString() `
            -WorkingDirectory $backendDir `
            -PassThru
        Write-Host "  Backend PID: $($backendProcess.Id)" -ForegroundColor Gray

        $token = $env:LOCAL_API_TOKEN
        if (-not $token) {
            $token = -join ((1..32) | ForEach-Object { "{0:x2}" -f (Get-Random -Maximum 256) })
            $env:LOCAL_API_TOKEN = $token
        }

        if (-not (Check-BackendHealth -port $Port -token $token)) {
            throw "Backend health check failed"
        }
    }

    if (-not $BackendOnly) {
        Write-Host "`nStarting Electron frontend..." -ForegroundColor Yellow
        $electronArgs = "."
        if ($Dev) { $electronArgs += " --dev" }
        
        $electronProcess = Start-Process -FilePath "npx" `
            -ArgumentList "electron", $electronArgs `
            -WorkingDirectory $ProjectRoot `
            -PassThru
        Write-Host "  Electron PID: $($electronProcess.Id)" -ForegroundColor Gray
    }

    if ($BackendOnly -or $FrontendOnly) {
        Write-Host "`nPress Ctrl+C to stop..." -ForegroundColor Gray
        while ($true) { Start-Sleep -Seconds 1 }
    } else {
        Write-Host "`nApplication started. Close the window or press Ctrl+C to stop." -ForegroundColor Green
        $electronProcess.WaitForExit()
        Stop-Processes
    }
}
catch {
    Write-Host "`nERROR: $_" -ForegroundColor Red
    Stop-Processes
    exit 1
}
finally {
    Stop-Processes
}