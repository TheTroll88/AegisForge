<#
.SYNOPSIS
    Manage AegisForge paper trading service.

.DESCRIPTION
    Start, stop, or check status of the paper trading background service.

.EXAMPLE
    .\manage_paper.ps1 start         # Start paper trading
    .\manage_paper.ps1 start -Hours 24  # Run for 24 hours
    .\manage_paper.ps1 stop          # Stop gracefully
    .\manage_paper.ps1 status        # Check if running
    .\manage_paper.ps1 logs          # Tail latest log
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet("start", "stop", "status", "logs")]
    [string]$Action = "status",

    [float]$Hours = 0,
    [int]$Delay = 3
)

$EngineDir = Join-Path $PSScriptRoot "engine"
$PidFile   = Join-Path $EngineDir "logs" "paper_service.pid"
$Python    = "python"

function Get-ServicePid {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile -ErrorAction SilentlyContinue
        if ($pid -and (Get-Process -Id $pid -ErrorAction SilentlyContinue)) {
            return [int]$pid
        }
    }
    return $null
}

switch ($Action) {
    "start" {
        $existing = Get-ServicePid
        if ($existing) {
            Write-Host "Already running (PID $existing)." -ForegroundColor Yellow
            return
        }

        $args = @("paper_service.py", "--delay", $Delay)
        if ($Hours -gt 0) {
            $args += @("--hours", $Hours)
        }

        Push-Location $EngineDir
        $proc = Start-Process -FilePath $Python -ArgumentList $args -WindowStyle Hidden -PassThru
        Pop-Location

        Start-Sleep -Seconds 2
        if (Get-Process -Id $proc.Id -ErrorAction SilentlyContinue) {
            Write-Host "Paper service started (PID $($proc.Id))." -ForegroundColor Green
        } else {
            Write-Host "Failed to start. Check logs." -ForegroundColor Red
        }
    }

    "stop" {
        $pid = Get-ServicePid
        if (-not $pid) {
            Write-Host "Not running." -ForegroundColor Yellow
            return
        }

        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        if (Test-Path $PidFile) { Remove-Item $PidFile -Force }
        Write-Host "Paper service stopped (was PID $pid)." -ForegroundColor Green
    }

    "status" {
        $pid = Get-ServicePid
        if ($pid) {
            $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
            $uptime = (Get-Date) - $proc.StartTime
            Write-Host "Running (PID $pid) | Uptime: $($uptime.ToString('hh\:mm\:ss'))" -ForegroundColor Green
        } else {
            Write-Host "Not running." -ForegroundColor Yellow
        }
    }

    "logs" {
        $logDir = Join-Path $EngineDir "logs"
        $latest = Get-ChildItem -Path $logDir -Filter "paper_service_*.log" -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 1

        if ($latest) {
            Write-Host "=== $($latest.Name) ===" -ForegroundColor Cyan
            Get-Content $latest.FullName -Tail 30
        } else {
            Write-Host "No logs found." -ForegroundColor Yellow
        }
    }
}
