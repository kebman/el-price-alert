# scripts\register_task.ps1
param(
  [string]$TaskName = "EL Price Alert",
  [string]$Time
)
$ErrorActionPreference = "Stop"

$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)

# Default time from config.json if omitted
if (-not $Time) {
  $cfgPath = Join-Path $root "config.json"
  if (Test-Path $cfgPath) {
    $cfg = Get-Content $cfgPath -Raw | ConvertFrom-Json
    if ($cfg.check_time) { $Time = $cfg.check_time } else { $Time = "15:00" }
  } else { $Time = "15:00" }
}

# Prefer local .venv python; otherwise rely on PATH
$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) { $py = "python" }

$script = Join-Path $root "run_alert.py"

# Parse HH:mm
$parts = $Time.Split(":")
if ($parts.Count -lt 2) { throw "Time must be HH:mm, got '$Time'" }
[int]$h = $parts[0]; [int]$m = $parts[1]

$trigger  = New-ScheduledTaskTrigger -Daily -At (Get-Date -Hour $h -Minute $m -Second 0)
$action   = New-ScheduledTaskAction -Execute $py -Argument "`"$script`""
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries
$task     = New-ScheduledTask -Action $action -Trigger $trigger -Settings $settings

Register-ScheduledTask -TaskName $TaskName -InputObject $task -Force | Out-Null
Write-Host "Registered task '$TaskName' at $Time daily (using $py)."