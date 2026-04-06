$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

. (Join-Path $scriptDir "common.ps1")

$taskName = Get-AngleFoundryTaskName
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue

if ($null -eq $task) {
    Write-Host "Scheduled task '$taskName' is not registered."
    exit 0
}

$info = Get-ScheduledTaskInfo -TaskName $taskName

Write-Host "TaskName: $($task.TaskName)"
Write-Host "State: $($task.State)"
Write-Host "LastRunTime: $($info.LastRunTime)"
Write-Host "LastTaskResult: $($info.LastTaskResult)"
Write-Host "NextRunTime: $($info.NextRunTime)"
Write-Host "Author: $($task.Principal.UserId)"
Write-Host "Command: $($task.Actions.Execute) $($task.Actions.Arguments)"

