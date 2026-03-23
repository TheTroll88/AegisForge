param(
    [int]$Rounds = 0,
    [int]$RestartDelaySeconds = 60,
    [ValidateSet("comprehension", "research")]
    [string]$Mode = "comprehension"
)

$ErrorActionPreference = "Continue"

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

$logsDir = Join-Path $root "logs"
$runtimeDir = Join-Path $root ".runtime"
$heartbeatFile = Join-Path $logsDir "miner_heartbeat.log"
$daemonLogFile = Join-Path $logsDir "miner_daemon.log"
$pidFile = Join-Path $runtimeDir "miner_daemon.pid"
$python = Join-Path $root ".venv\Scripts\python.exe"
$miner = Join-Path $root "litcoin_miner.py"

New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
New-Item -ItemType Directory -Path $runtimeDir -Force | Out-Null

# Global mutex prevents duplicate daemon instances started by task scheduler races.
$createdNew = $false
try {
    $daemonMutex = New-Object System.Threading.Mutex($false, "Global\LITCOIN_Miner_Daemon_Lock", [ref]$createdNew)
}
catch {
    Write-Host "Failed to create daemon mutex: $($_.Exception.Message)"
    exit 1
}

if (-not $createdNew) {
    Write-Host "Another daemon instance already holds the global lock. Exiting."
    exit 0
}

$existingPid = $null
if (Test-Path $pidFile) {
    try {
        $existingPid = [int](Get-Content -Path $pidFile -Raw)
    }
    catch {
        $existingPid = $null
    }
}

if ($existingPid) {
    $existing = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
    if ($existing) {
        Write-Host "Daemon already running with PID $existingPid"
        exit 0
    }
}

$PID | Set-Content -Path $pidFile -Encoding ascii

function Write-Heartbeat {
    param(
        [string]$State,
        [string]$Info
    )

    $line = "{0} | state={1} | info={2}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $State, $Info
    Add-Content -Path $heartbeatFile -Value $line -Encoding utf8
    Write-Host $line
}

if ([string]::IsNullOrWhiteSpace($env:BANKR_API_KEY)) {
    Write-Heartbeat -State "error" -Info "BANKR_API_KEY not set in this process"
    exit 1
}

# Force UTF-8 so emoji/status output from the miner does not crash in cp1252 consoles.
[Console]::InputEncoding = [System.Text.UTF8Encoding]::new($false)
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

Write-Heartbeat -State "start" -Info "daemon started pid=$PID rounds=$Rounds"

if ($Mode -eq "research" -and [string]::IsNullOrWhiteSpace($env:AI_API_KEY)) {
    Write-Heartbeat -State "error" -Info "research mode requires AI_API_KEY (set in env or vault)"
    exit 1
}

while ($true) {
    # Kill any orphaned litcoin_miner.py processes before starting fresh
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'litcoin_miner\.py' } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 800

    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path $daemonLogFile -Value ("`n===== RUN {0} =====" -f $ts) -Encoding utf8
    Write-Heartbeat -State "running" -Info "starting miner (mode=$Mode rounds=$Rounds)"

    if ($Mode -eq "research") {
        # Research mode defaults to infinite loop unless caller overrides via task args.
        $minerArgs = @("-X", "utf8", $miner, "--research", "--loop", "--rounds", "0")
    }
    else {
        # rounds=0 → mine() runs indefinitely, handling cap/reset internally.
        $minerArgs = @("-X", "utf8", $miner, "--rounds-comp", "$Rounds")
    }

    $runLogFile = Join-Path $runtimeDir "miner_run_output.log"
    if (Test-Path $runLogFile) {
        Remove-Item $runLogFile -Force -ErrorAction SilentlyContinue
    }

    # Start miner detached so daemon can monitor output freshness.
    $proc = Start-Process -FilePath $python -ArgumentList $minerArgs -PassThru -NoNewWindow -RedirectStandardOutput $runLogFile -RedirectStandardError $runLogFile

    $startTime = Get-Date
    $lastObservedWrite = $startTime
    $heartbeatMissLogged = $false
    $lastClaimTime = $startTime

    while (-not $proc.HasExited) {
        Start-Sleep -Seconds 30

        if (Test-Path $runLogFile) {
            try {
                $info = Get-Item $runLogFile
                if ($info.LastWriteTime -gt $lastObservedWrite) {
                    $lastObservedWrite = $info.LastWriteTime
                    $heartbeatMissLogged = $false
                }
            }
            catch {
                # Keep loop alive; next cycle will re-check.
            }
        }

        $silentFor = (Get-Date) - $lastObservedWrite
        if (-not $heartbeatMissLogged -and $silentFor.TotalMinutes -ge 35) {
            Write-Heartbeat -State "warning" -Info "heartbeat missed (no miner output for 35+ minutes); restarting miner"
            try {
                Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
            }
            catch {
            }
            $heartbeatMissLogged = $true
        }

        # Auto-claim every 30 minutes
        $timeSinceClaim = (Get-Date) - $lastClaimTime
        if ($timeSinceClaim.TotalMinutes -ge 30) {
            Write-Heartbeat -State "claim" -Info "running scheduled auto-claim"
            try {
                $claimArgs = @("-X", "utf8", $miner, "--claim")
                $claimResult = & $python @claimArgs 2>&1 | Out-String
                $lastClaimTime = Get-Date
                if ($claimResult -match "No claimable") {
                    Write-Heartbeat -State "claim" -Info "nothing to claim"
                }
                elseif ($claimResult -match "claimed successfully") {
                    Write-Heartbeat -State "claim" -Info "rewards claimed successfully"
                    Add-Content -Path $daemonLogFile -Value ("[CLAIM] {0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $claimResult.Trim()) -Encoding utf8
                }
                else {
                    Write-Heartbeat -State "claim" -Info "claim completed"
                    Add-Content -Path $daemonLogFile -Value ("[CLAIM] {0} {1}" -f (Get-Date -Format "yyyy-MM-dd HH:mm:ss"), $claimResult.Trim()) -Encoding utf8
                }
            }
            catch {
                Write-Heartbeat -State "claim-error" -Info "auto-claim failed: $($_.Exception.Message)"
            }
        }
    }

    if (Test-Path $runLogFile) {
        Get-Content -Path $runLogFile -ErrorAction SilentlyContinue | Out-File -FilePath $daemonLogFile -Encoding utf8 -Append
    }

    $exitCode = $proc.ExitCode

    if ($exitCode -eq 0) {
        Write-Heartbeat -State "restart" -Info "miner exited cleanly, restarting in $RestartDelaySeconds seconds"
    }
    else {
        Write-Heartbeat -State "error" -Info "miner crashed exit=$exitCode, restarting in $RestartDelaySeconds seconds"
    }

    Start-Sleep -Seconds $RestartDelaySeconds
}
