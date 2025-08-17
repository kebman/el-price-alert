# scripts\unregiser_task.ps1
param([string]$TaskName = "EL Price Alert")
if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
  Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
  Write-Host "Removed task '$TaskName'."
} else {
  Write-Host "Task '$TaskName' not found."
}