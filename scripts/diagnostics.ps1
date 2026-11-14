<# 
.SYNOPSIS
    Run diagnostics for Global Airdrop Hunter

.DESCRIPTION
    Checks system health, database integrity, API connectivity, and configuration.

.NOTES
    Run from project root: E:\Global Airdrop Hunter
#>

param(
    [switch]$Verbose,
    [switch]$Fix
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent
$ProjectRoot = Resolve-Path $ProjectRoot

$venvPath = Join-Path $ProjectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$backendDir = Join-Path $ProjectRoot "backend"
$dbPath = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\app.db"
$logDir = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\logs"

Write-Host "=== Global Airdrop Hunter - Diagnostics ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray
Write-Host "Timestamp: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Gray
Write-Host ""

$checks = @()
$passed = 0
$failed = 0
$warnings = 0

function Add-Check {
    param([string]$Name, [bool]$Result, [string]$Message, [string]$Level = "INFO")
    $checks += @{ Name = $Name; Result = $Result; Message = $Message; Level = $Level }
    if ($Result) { $script:passed++ } else { if ($Level -eq "ERROR") { $script:failed++ } else { $script:warnings++ } }
}

Write-Host "Checking prerequisites..." -ForegroundColor Yellow
Add-Check "Python 3.12" (Test-Path "$venvPath\Scripts\python.exe") "Virtual environment exists" "ERROR"
Add-Check "Node.js" (Get-Command node -ErrorAction SilentlyContinue) "Node.js in PATH"
Add-Check "npm" (Get-Command npm -ErrorAction SilentlyContinue) "npm in PATH"
Add-Check "Git" (Get-Command git -ErrorAction SilentlyContinue) "Git in PATH"

Write-Host "`nChecking project structure..." -ForegroundColor Yellow
Add-Check "package.json" (Test-Path "$ProjectRoot\package.json") "Electron config exists"
Add-Check "backend/main.py" (Test-Path "$ProjectRoot\backend\main.py") "FastAPI entry point exists"
Add-Check "desktop/main.js" (Test-Path "$ProjectRoot\desktop\main.js") "Electron main process exists"
Add-Check "desktop/preload.js" (Test-Path "$ProjectRoot\desktop\preload.js") "Electron preload script exists"
Add-Check "frontend/index.html" (Test-Path "$ProjectRoot\frontend\index.html") "Frontend entry point exists"

Write-Host "`nChecking database..." -ForegroundColor Yellow
$dbExists = Test-Path $dbPath
Add-Check "Database file" $dbExists "Database at $dbPath" "ERROR"

if ($dbExists) {
    try {
        $integrity = & $pythonExe -c "
import sqlite3
conn = sqlite3.connect(r'$dbPath')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
result = cursor.fetchone()[0]
conn.close()
print(result)
" -ErrorAction Stop
        Add-Check "Database integrity" ($integrity -eq "ok") "Integrity check: $integrity" "ERROR"
    } catch {
        Add-Check "Database integrity" $false "Failed to check integrity: $_" "ERROR"
    }

    try {
        $tableCount = & $pythonExe -c "
import sqlite3
conn = sqlite3.connect(r'$dbPath')
cursor = conn.cursor()
cursor.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table'\")
count = cursor.fetchone()[0]
conn.close()
print(count)
" -ErrorAction Stop
        Add-Check "Database tables" ($tableCount -ge 10) "Found $tableCount tables"
    } catch {
        Add-Check "Database tables" $false "Failed to count tables: $_" "WARNING"
    }

    try {
        $campaignCount = & $pythonExe -c "
import sqlite3
conn = sqlite3.connect(r'$dbPath')
cursor = conn.cursor()
cursor.execute('SELECT COUNT(*) FROM campaigns')
count = cursor.fetchone()[0]
conn.close()
print(count)
" -ErrorAction Stop
        Add-Check "Campaign data" ($campaignCount -ge 0) "Campaigns in database: $campaignCount"
    } catch {
        Add-Check "Campaign data" $false "Failed to count campaigns: $_" "WARNING"
    }
}

Write-Host "`nChecking data directories..." -ForegroundColor Yellow
$dirs = @(
    @{ Path = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter"; Name = "App Data" },
    @{ Path = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\backups"; Name = "Backups" },
    @{ Path = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\logs"; Name = "Logs" }
)

foreach ($dir in $dirs) {
    $exists = Test-Path $dir.Path
    Add-Check $dir.Name $exists "Directory: $($dir.Path)" "WARNING"
    if (-not $exists -and $Fix) {
        New-Item -ItemType Directory -Path $dir.Path -Force | Out-Null
        Write-Host "  Created missing directory" -ForegroundColor Green
    }
}

Write-Host "`nChecking backend API (if running)..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/health" -Method Get -TimeoutSec 3 -ErrorAction Stop
    Add-Check "API Health Endpoint" ($response.status -eq "healthy") "API responding: $($response.status)"
    Add-Check "API Version" ($response.version -ne $null) "Version: $($response.version)"
    Add-Check "Database Connected" ($response.database -eq "connected") "Database: $($response.database)"
} catch {
    Add-Check "API Health Endpoint" $false "API not responding (backend may not be running)" "WARNING"
}

Write-Host "`nChecking Electron build..." -ForegroundColor Yellow
Add-Check "node_modules" (Test-Path "$ProjectRoot\node_modules") "Dependencies installed"
Add-Check "electron binary" (Test-Path "$ProjectRoot\node_modules\.bin\electron.cmd") "Electron available"

Write-Host "`n=== SUMMARY ===" -ForegroundColor Cyan
Write-Host "Passed:  $passed" -ForegroundColor Green
Write-Host "Warnings: $warnings" -ForegroundColor Yellow
Write-Host "Failed:  $failed" -ForegroundColor Red

if ($Verbose) {
    Write-Host "`nDetailed Results:" -ForegroundColor Gray
    foreach ($check in $checks) {
        $color = if ($check.Result) { "Green" } elseif ($check.Level -eq "ERROR") { "Red" } else { "Yellow" }
        $status = if ($check.Result) { "✓" } else { "✗" }
        Write-Host "  $status $($check.Name): $($check.Message)" -ForegroundColor $color
    }
}

if ($failed -gt 0) {
    Write-Host "`n⚠ Some checks failed. Run with -Fix to attempt repairs." -ForegroundColor Yellow
    exit 1
} elseif ($warnings -gt 0) {
    Write-Host "`n⚠ Some checks passed with warnings." -ForegroundColor Yellow
    exit 0
} else {
    Write-Host "`n✓ All checks passed." -ForegroundColor Green
    exit 0
}