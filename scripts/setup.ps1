<# 
.SYNOPSIS
    One-time environment setup for Global Airdrop Hunter

.DESCRIPTION
    Creates virtual environment, installs dependencies, initializes database,
    and prepares the application for first run.

.NOTES
    Run from project root: E:\Global Airdrop Hunter
    Requires: Python 3.12, Node.js, npm, Git
#>

param(
    [switch]$Force,
    [switch]$SkipNode,
    [switch]$SkipPython,
    [switch]$SkipDatabase
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Definition | Split-Path -Parent
$ProjectRoot = Resolve-Path $ProjectRoot

Write-Host "=== Global Airdrop Hunter - Environment Setup ===" -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

function Test-Command {
    param([string]$Command, [string]$Name)
    try {
        $result = & $Command 2>$null
        Write-Host "  ✓ $Name found" -ForegroundColor Green
        return $true
    } catch {
        Write-Host "  ✗ $Name NOT found" -ForegroundColor Red
        return $false
    }
}

Write-Host "`nChecking prerequisites..." -ForegroundColor Yellow
$pythonOk = Test-Command "py -3.12 --version" "Python 3.12"
$nodeOk = Test-Command "node --version" "Node.js"
$npmOk = Test-Command "npm --version" "npm"
$gitOk = Test-Command "git --version" "Git"

if (-not $pythonOk) {
    Write-Host "`nERROR: Python 3.12 is required but not found." -ForegroundColor Red
    Write-Host "Install from https://python.org/downloads/windows/" -ForegroundColor Yellow
    exit 1
}

if (-not $nodeOk -or -not $npmOk) {
    Write-Host "`nWARNING: Node.js/npm not found. Electron build will not work." -ForegroundColor Yellow
}

if (-not $gitOk) {
    Write-Host "`nWARNING: Git not found. Version control will not work." -ForegroundColor Yellow
}

if (-not $SkipPython) {
    Write-Host "`nSetting up Python virtual environment..." -ForegroundColor Yellow
    $venvPath = Join-Path $ProjectRoot ".venv"
    
    if (Test-Path $venvPath -and -not $Force) {
        Write-Host "  Virtual environment already exists. Use -Force to recreate." -ForegroundColor Yellow
    } else {
        if (Test-Path $venvPath) {
            Write-Host "  Removing existing virtual environment..." -ForegroundColor Gray
            Remove-Item $venvPath -Recurse -Force
        }
        Write-Host "  Creating virtual environment at $venvPath..." -ForegroundColor Gray
        & py -3.12 -m venv $venvPath
        Write-Host "  ✓ Virtual environment created" -ForegroundColor Green
    }

    Write-Host "  Upgrading pip..." -ForegroundColor Gray
    & "$venvPath\Scripts\python.exe" -m pip install --upgrade pip --quiet

    Write-Host "  Installing Python dependencies..." -ForegroundColor Gray
    & "$venvPath\Scripts\pip.exe" install -r "$ProjectRoot\backend\requirements.txt"
    Write-Host "  ✓ Python dependencies installed" -ForegroundColor Green
}

if (-not $SkipNode) {
    Write-Host "`nInstalling Node.js dependencies..." -ForegroundColor Yellow
    if (Test-Path "$ProjectRoot\node_modules" -and -not $Force) {
        Write-Host "  node_modules already exists. Use -Force to reinstall." -ForegroundColor Yellow
    } else {
        if (Test-Path "$ProjectRoot\node_modules") {
            Write-Host "  Removing existing node_modules..." -ForegroundColor Gray
            Remove-Item "$ProjectRoot\node_modules" -Recurse -Force
        }
        if (Test-Path "$ProjectRoot\package-lock.json") {
            Remove-Item "$ProjectRoot\package-lock.json" -Force
        }
        Write-Host "  Running npm install..." -ForegroundColor Gray
        Set-Location $ProjectRoot
        & npm install
        Write-Host "  ✓ Node.js dependencies installed" -ForegroundColor Green
    }
}

if (-not $SkipDatabase) {
    Write-Host "`nInitializing database..." -ForegroundColor Yellow
    $appData = [Environment]::GetFolderPath('LocalApplicationData')
    $dbDir = Join-Path $appData "GlobalAirdropHunter"
    $dbPath = Join-Path $dbDir "app.db"
    
    if (-not (Test-Path $dbDir)) {
        New-Item -ItemType Directory -Path $dbDir -Force | Out-Null
        Write-Host "  Created data directory: $dbDir" -ForegroundColor Green
    }
    
    if (Test-Path $dbPath -and -not $Force) {
        Write-Host "  Database already exists. Use -Force to reinitialize." -ForegroundColor Yellow
    } else {
        Write-Host "  Running database initialization..." -ForegroundColor Gray
        $env:PYTHONPATH = "$ProjectRoot\backend"
        $env:DATABASE_PATH = $dbPath
        & "$venvPath\Scripts\python.exe" -c "
import sys
sys.path.insert(0, r'$ProjectRoot\backend')
from backend.database import init_database
init_database()
print('Database initialized successfully')
"
        Write-Host "  ✓ Database initialized at $dbPath" -ForegroundColor Green
    }
}

Write-Host "`n=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "To start the application, run:" -ForegroundColor Gray
Write-Host "  .\scripts\start.ps1" -ForegroundColor White
Write-Host "" -ForegroundColor Gray
Write-Host "To build the installer, run:" -ForegroundColor Gray
Write-Host "  npm run build" -ForegroundColor White