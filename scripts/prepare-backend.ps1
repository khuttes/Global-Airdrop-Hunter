# Prepare backend for packaging
# Ensures Python virtual environment is ready and dependencies are installed

Write-Host "=== Preparing Backend for Packaging ==="

$projectRoot = "E:\Global Airdrop Hunter"
$venvDir = Join-Path $projectRoot ".venv"
$venvScripts = Join-Path $venvDir "Scripts"
$pythonExe = Join-Path $venvScripts "python.exe"

# Check if virtual environment exists
if (-not (Test-Path $venvDir)) {
    Write-Host "Virtual environment not found. Creating..."
    & python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment"
        exit 1
    }
}

# Upgrade pip using python -m pip
Write-Host "Upgrading pip..."
& $pythonExe -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Failed to upgrade pip, continuing..."
}

# Install backend dependencies using python -m pip
Write-Host "Installing backend dependencies..."
& $pythonExe -m pip install -r (Join-Path $projectRoot "backend\requirements.txt")
if ($LASTEXITCODE -ne 0) {
    Write-Error "Failed to install backend dependencies"
    exit 1
}

# Verify Python executable exists
if (-not (Test-Path $pythonExe)) {
    Write-Error "Python executable not found in virtual environment"
    exit 1
}

# Test backend import
Write-Host "Testing backend imports..."
& $pythonExe -c "
import sys
sys.path.insert(0, 'backend')
from backend.main import create_app
from backend.config import get_settings
print('Backend imports OK')
"
if ($LASTEXITCODE -ne 0) {
    Write-Error "Backend import test failed"
    exit 1
}

Write-Host "=== Backend preparation complete ==="
Write-Host "Python executable: $pythonExe"
Write-Host "Virtual environment: $venvDir"