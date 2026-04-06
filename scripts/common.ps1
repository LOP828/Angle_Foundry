function Get-EnvValue {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Name
    )

    $processValue = [Environment]::GetEnvironmentVariable($Name, "Process")
    if (-not [string]::IsNullOrWhiteSpace($processValue)) {
        return $processValue
    }

    $userValue = [Environment]::GetEnvironmentVariable($Name, "User")
    if (-not [string]::IsNullOrWhiteSpace($userValue)) {
        return $userValue
    }

    $machineValue = [Environment]::GetEnvironmentVariable($Name, "Machine")
    if (-not [string]::IsNullOrWhiteSpace($machineValue)) {
        return $machineValue
    }

    return $null
}

function Import-AngleFoundryEnv {
    $requiredVariables = @(
        "ANGLE_FOUNDRY_API_KEY",
        "ANGLE_FOUNDRY_AI_BASE_URL",
        "ANGLE_FOUNDRY_AI_MODEL",
        "FEISHU_WEBHOOK"
    )

    $missingVariables = @()
    foreach ($name in $requiredVariables) {
        $value = Get-EnvValue -Name $name
        if ([string]::IsNullOrWhiteSpace($value)) {
            $missingVariables += $name
            continue
        }

        [Environment]::SetEnvironmentVariable($name, $value, "Process")
    }

    if ($missingVariables.Count -gt 0) {
        throw "Missing required environment variables: $($missingVariables -join ', ')"
    }

    [Environment]::SetEnvironmentVariable("UV_CACHE_DIR", ".uv-cache", "Process")
}

function Get-AngleFoundryTaskName {
    return "AngleFoundryScheduler"
}

function Get-AngleFoundryUserName {
    return [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
}

