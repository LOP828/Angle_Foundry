$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir

. (Join-Path $scriptDir "common.ps1")

$taskName = Get-AngleFoundryTaskName
$currentUser = Get-AngleFoundryUserName
$schedulerScript = Join-Path $scriptDir "start_scheduler.ps1"
$powerShellPath = Join-Path $env:WINDIR "System32\WindowsPowerShell\v1.0\powershell.exe"
$argument = '-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File "{0}"' -f $schedulerScript

$action = New-ScheduledTaskAction -Execute $powerShellPath -Argument $argument
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -MultipleInstances IgnoreNew

try {
    Register-ScheduledTask `
        -TaskName $taskName `
        -Action $action `
        -Trigger $trigger `
        -Principal $principal `
        -Settings $settings `
        -Description "Start Angle Foundry scheduler at user logon." `
        -Force `
        -ErrorAction Stop | Out-Null
} catch {
    Write-Error "Failed to register scheduled task '$taskName': $($_.Exception.Message)"
    exit 1
}

Write-Host "Registered scheduled task '$taskName' for user '$currentUser'."
Write-Host "Scheduler script: $schedulerScript"
Write-Host "Project root: $repoRoot"
