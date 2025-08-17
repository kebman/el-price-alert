# scripts\run_now.ps1
param([switch]$Verbose)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Prefer local .venv; fall back to system python
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

if ($Verbose) { Write-Host "Using Python: $py" }

& $py (Join-Path $root "run_alert.py") @Args
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }