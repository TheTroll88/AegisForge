$ErrorActionPreference = 'SilentlyContinue'

$targets = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -match 'miner_daemon\.ps1|litcoin_miner\.py'
}

foreach ($p in $targets) {
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
}

$pidFile = Join-Path $PSScriptRoot '.runtime\miner_daemon.pid'
if (Test-Path $pidFile) {
    Remove-Item $pidFile -Force -ErrorAction SilentlyContinue
}

Write-Output ('Stopped process count: ' + $targets.Count)
Write-Output 'Cleared runtime pid file (if present).'
