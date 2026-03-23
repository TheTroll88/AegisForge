param(
    [int]$CheckIntervalMinutes = 5
)

$ErrorActionPreference = "Stop"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$runtimeDir = Join-Path $root ".runtime"
$logsDir = Join-Path $root "logs"
$pidFile = Join-Path $runtimeDir "miner_daemon.pid"
$daemonScript = Join-Path $root "miner_daemon.ps1"
$vaultScript = Join-Path $root "secure_vault.ps1"
$ensureLog = Join-Path $logsDir "ensure_daemon.log"

New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null
New-Item -ItemType Directory -Path $logsDir -Force | Out-Null

function Write-EnsureLog {
    param([string]$Message)
    $line = "{0} | {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $Message
    Add-Content -Path $ensureLog -Value $line -Encoding utf8
}

function Test-DaemonRunning {
    $all = @(Get-DaemonProcesses)
    if ($all.Count -gt 0) {
        $current = $all | Sort-Object ProcessId -Descending | Select-Object -First 1
        if ($current) {
            $current.ProcessId | Set-Content -Path $pidFile -Encoding ascii
            return $true
        }
    }

    if (-not (Test-Path $pidFile)) {
        return $false
    }

    $pidText = Get-Content -Path $pidFile -Raw -ErrorAction SilentlyContinue
    if ([string]::IsNullOrWhiteSpace($pidText)) {
        return $false
    }

    $procId = 0
    if (-not [int]::TryParse($pidText.Trim(), [ref]$procId)) {
        return $false
    }

    $proc = Get-CimInstance Win32_Process -Filter "ProcessId=$procId" -ErrorAction SilentlyContinue
    if (-not $proc) {
        return $false
    }

    return ($proc.CommandLine -match "miner_daemon\.ps1")
}

function Get-DaemonProcesses {
    Get-CimInstance Win32_Process -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "miner_daemon\.ps1" }
}

function Resolve-DaemonState {
    $all = @(Get-DaemonProcesses)
    if ($all.Count -le 1) {
        return
    }

    $keep = $all | Sort-Object ProcessId -Descending | Select-Object -First 1
    $kill = $all | Where-Object { $_.ProcessId -ne $keep.ProcessId }

    foreach ($p in $kill) {
        Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
        Write-EnsureLog ("killed duplicate daemon pid={0}" -f $p.ProcessId)
    }

    $keep.ProcessId | Set-Content -Path $pidFile -Encoding ascii
}

Resolve-DaemonState

if (Test-DaemonRunning) {
    $currentPid = (Get-DaemonProcesses | Sort-Object ProcessId -Descending | Select-Object -First 1).ProcessId
    if ($currentPid) {
        $currentPid | Set-Content -Path $pidFile -Encoding ascii
    }
    Write-EnsureLog "daemon already running"
    exit 0
}

$bankrKey = powershell -NoProfile -ExecutionPolicy Bypass -File $vaultScript -Action get -Name BANKR_API_KEY 2>$null
if ([string]::IsNullOrWhiteSpace($bankrKey)) {
    Write-EnsureLog "cannot start daemon: BANKR_API_KEY missing from vault"
    exit 1
}

$env:BANKR_API_KEY = $bankrKey

$persistedModel = [System.Environment]::GetEnvironmentVariable("MODEL", "User")
if (-not [string]::IsNullOrWhiteSpace($persistedModel)) {
    $env:MODEL = $persistedModel
}

$startArgs = @(
    "-NoProfile",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$daemonScript`""
)

Start-Process -FilePath "powershell.exe" -ArgumentList $startArgs -WorkingDirectory $root -WindowStyle Hidden | Out-Null
Start-Sleep -Seconds 2

if (Test-DaemonRunning) {
    Write-EnsureLog "daemon started by watchdog"
    exit 0
}

Write-EnsureLog "daemon start attempted but no healthy pid detected"
exit 1
