<# 
.SYNOPSIS
    Stop Global Airdrop Hunter application

.DESCRIPTION
    Gracefully stops the Electron frontend and FastAPI backend processes.

.NOTES
    Run from project root: E:\Global Airdrop Hunter
#>

param(
    [switch]$Force
)

$ErrorActionPreference = "Continue"

Write-Host "=== Global Airdrop Hunter - Stopping Application ===" -ForegroundColor Cyan

$processes = @(
    @{ Name = "Electron"; Pattern = "electron" },
    @{ Name = "Python (uvicorn)"; Pattern = "uvicorn" },
    @{ Name = "Python (main.py)"; Pattern = "main.py" }
)

$foundAny = $false

foreach ($proc in $processes) {
    $pids = Get-Process -Name $proc.Pattern -ErrorAction SilentlyContinue | Where-Object {
        $_.Path -like "*Global Airdrop Hunter*" -or $_.Path -like "*GlobalAirdropHunter*"
    } | Select-Object -ExpandProperty Id

    if ($pids) {
        $foundAny = $true
        foreach ($processId in $pids) {
            try {
                if ($Force) {
                    Stop-Process -Id $processId -Force
                    Write-Host "  Force killed $($proc.Name) (PID: $processId)" -ForegroundColor Yellow
                } else {
                    Stop-Process -Id $processId
                    Write-Host "  Stopped $($proc.Name) (PID: $processId)" -ForegroundColor Green
                }
            } catch {
                Write-Host "  Failed to stop $($proc.Name) (PID: $processId): $_" -ForegroundColor Red
            }
        }
    }
}

if (-not $foundAny) {
    Write-Host "No running Global Airdrop Hunter processes found." -ForegroundColor Yellow
}

Write-Host "`nDone." -ForegroundColor Cyan