$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent $scriptDir

. (Join-Path $scriptDir "common.ps1")

Set-Location $repoRoot
Import-AngleFoundryEnv

uv run python -m app.main
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    Write-Error "Scheduler startup failed with exit code $exitCode."
}

exit $exitCode

