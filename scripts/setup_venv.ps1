# scripts\setup_venv.ps1
param(
  [string]$Python = "python",
  [string]$VenvPath = ".\.venv"   # public default: local venv inside repo
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Normalize path
$venvFull = Resolve-Path -LiteralPath $VenvPath -ErrorAction SilentlyContinue
if (-not $venvFull) {
  New-Item -ItemType Directory -Force -Path $VenvPath | Out-Null
  $venvFull = Resolve-Path -LiteralPath $VenvPath
}

Write-Host "Creating/using venv at: $($venvFull.Path)"

if (-not (Test-Path "$($venvFull.Path)\Scripts\python.exe")) {
  & $Python -m venv "$($venvFull.Path)"
}

& "$($venvFull.Path)\Scripts\python.exe" -m pip install --upgrade pip
& "$($venvFull.Path)\Scripts\pip.exe" install -r "$root\requirements.txt"

Write-Host "Done."
