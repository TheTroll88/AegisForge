<# 
.SYNOPSIS
    Manage the Auto-Organizer daemon (start/stop/status/install)
.DESCRIPTION
    Controls the file auto-organizer that watches D:\DataVault\Dropbox
    and sorts files into D:\DataVault\Organized\{Category}\
#>

param(
    [ValidateSet("start", "stop", "status", "install", "uninstall", "once")]
    [string]$Action = "status"
)

$PythonExe = "python"
$ScriptPath = Join-Path $PSScriptRoot "auto_organizer.py"
$PidFile = Join-Path $env:TEMP "auto_organizer.pid"
$TaskName = "AutoOrganizer"

function Start-Daemon {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Daemon already running (PID $pid)" -ForegroundColor Yellow
            return
        }
        Remove-Item $PidFile -Force
    }
    
    $proc = Start-Process $PythonExe -ArgumentList $ScriptPath -WindowStyle Hidden -PassThru
    Write-Host "Daemon started (PID $($proc.Id))" -ForegroundColor Green
    Write-Host "Watching: D:\DataVault\Dropbox"
    Write-Host "Sorting to: D:\DataVault\Organized\{Category}\"
}

function Stop-Daemon {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        Stop-Process -Id $pid -Force -ErrorAction SilentlyContinue
        Remove-Item $PidFile -Force
        Write-Host "Daemon stopped." -ForegroundColor Green
    }
    else {
        # Try to find by command line
        $procs = Get-Process python -ErrorAction SilentlyContinue | Where-Object {
            try { (Get-CimInstance Win32_Process -Filter "ProcessId=$($_.Id)").CommandLine -like "*auto_organizer*" } catch { $false }
        }
        if ($procs) {
            $procs | Stop-Process -Force
            Write-Host "Daemon stopped (found by name)." -ForegroundColor Green
        }
        else {
            Write-Host "Daemon not running." -ForegroundColor Yellow
        }
    }
}

function Get-DaemonStatus {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Daemon RUNNING (PID $pid, CPU: $([math]::Round($proc.CPU, 1))s)" -ForegroundColor Green
        }
        else {
            Write-Host "Daemon NOT RUNNING (stale PID file)" -ForegroundColor Red
            Remove-Item $PidFile -Force
        }
    }
    else {
        Write-Host "Daemon NOT RUNNING" -ForegroundColor Yellow
    }
    
    # Show dropbox status
    $dropbox = "D:\DataVault\Dropbox"
    if (Test-Path $dropbox) {
        $count = (Get-ChildItem $dropbox -Recurse -File -ErrorAction SilentlyContinue).Count
        Write-Host "Dropbox items waiting: $count"
    }
    
    # Show organized stats
    $organized = "D:\DataVault\Organized"
    if (Test-Path $organized) {
        $cats = Get-ChildItem $organized -Directory -ErrorAction SilentlyContinue
        foreach ($cat in $cats) {
            $fc = (Get-ChildItem $cat.FullName -File -ErrorAction SilentlyContinue).Count
            if ($fc -gt 0) {
                Write-Host "  $($cat.Name): $fc files"
            }
        }
    }
}

function Install-ScheduledTask {
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    $action = New-ScheduledTaskAction -Execute $PythonExe -Argument $ScriptPath
    $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable
    
    Register-ScheduledTask -TaskName $TaskName -Trigger $trigger -Action $action -Settings $settings -Description "Auto-organizer daemon for D:\DataVault\Dropbox" -Force
    Write-Host "Scheduled task '$TaskName' installed (runs at logon)" -ForegroundColor Green
}

function Uninstall-ScheduledTask {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "Scheduled task '$TaskName' removed" -ForegroundColor Green
}

switch ($Action) {
    "start" { Start-Daemon }
    "stop" { Stop-Daemon }
    "status" { Get-DaemonStatus }
    "install" { Install-ScheduledTask }
    "uninstall" { Uninstall-ScheduledTask }
    "once" { & $PythonExe $ScriptPath once }
}
