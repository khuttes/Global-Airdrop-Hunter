<# 
.SYNOPSIS
    Backup Global Airdrop Hunter database

.DESCRIPTION
    Creates a timestamped backup of the SQLite database.

.NOTES
    Run from project root: E:\Global Airdrop Hunter
#>

param(
    [string]$OutputDir,
    [switch]$Verify
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent
$ProjectRoot = Resolve-Path $ProjectRoot

$venvPath = Join-Path $ProjectRoot ".venv"
$pythonExe = Join-Path $venvPath "Scripts\python.exe"
$backendDir = Join-Path $ProjectRoot "backend"
$dbPath = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\app.db"

if (-not (Test-Path $dbPath)) {
    Write-Host "ERROR: Database not found at $dbPath" -ForegroundColor Red
    exit 1
}

if (-not $OutputDir) {
    $OutputDir = Join-Path $env:LOCALAPPDATA "GlobalAirdropHunter\backups"
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupName = "app_$timestamp.db"
$backupPath = Join-Path $OutputDir $backupName

Write-Host "=== Global Airdrop Hunter - Database Backup ===" -ForegroundColor Cyan
Write-Host "Source: $dbPath" -ForegroundColor Gray
Write-Host "Destination: $backupPath" -ForegroundColor Gray

try {
    Copy-Item -Path $dbPath -Destination $backupPath -Force
    Write-Host "  ✓ Database copied" -ForegroundColor Green

    if ($Verify) {
        Write-Host "  Verifying backup integrity..." -ForegroundColor Gray
        $result = & $pythonExe -c "
import sqlite3
conn = sqlite3.connect(r'$backupPath')
cursor = conn.cursor()
cursor.execute('PRAGMA integrity_check')
result = cursor.fetchone()
print('Integrity:', result[0])
cursor.execute('SELECT COUNT(*) FROM campaigns')
count = cursor.fetchone()[0]
print('Campaigns:', count)
conn.close()
"
        Write-Host "  $result" -ForegroundColor Green
    }

    $size = (Get-Item $backupPath).Length
    Write-Host "`nBackup complete: $backupPath ($([math]::Round($size/1KB, 2)) KB)" -ForegroundColor Cyan
}
catch {
    Write-Host "`nERROR: $_" -ForegroundColor Red
    exit 1
}