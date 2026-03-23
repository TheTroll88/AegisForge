@echo off
REM LITCOIN Miner Launcher for Windows
set "NO_PAUSE=0"
for %%A in (%1 %2 %3 %4 %5 %6) do (
    if /I "%%~A"=="--nopause" set "NO_PAUSE=1"
)

set "ARG2=%2"
set "ARG3=%3"
set "ARG4=%4"
set "ARG5=%5"
set "ARG6=%6"
if /I "%ARG2%"=="--nopause" set "ARG2="
if /I "%ARG3%"=="--nopause" set "ARG3="
if /I "%ARG4%"=="--nopause" set "ARG4="
if /I "%ARG5%"=="--nopause" set "ARG5="
if /I "%ARG6%"=="--nopause" set "ARG6="

for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0secure_vault.ps1" -Action get -Name BANKR_API_KEY 2^>nul`) do set "BANKR_API_KEY=%%I"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0secure_vault.ps1" -Action get -Name BANKR_LLM_KEY 2^>nul`) do set "BANKR_LLM_KEY=%%I"

for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0secure_vault.ps1" -Action get -Name AI_API_KEY 2^>nul`) do set "AI_API_KEY=%%I"

set "PYTHONUTF8=1"
set "PYTHONIOENCODING=utf-8"

if not defined BANKR_SESSION_COOKIE (
    for /f "usebackq delims=" %%I in (`powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0secure_vault.ps1" -Action get -Name BANKR_SESSION_COOKIE 2^>nul`) do set "BANKR_SESSION_COOKIE=%%I"
)

if not defined BANKR_API_KEY (
    echo.
    echo [ERROR] BANKR_API_KEY not set and not found in secure vault.
    echo.
    echo Save a key securely with:
    echo   powershell -ExecutionPolicy Bypass -File secure_vault.ps1 -Action setprompt -Name BANKR_API_KEY
    echo.
    pause
    exit /b 1
)

set "RUNTIME_DIR=%~dp0.runtime"
set "PID_FILE=%RUNTIME_DIR%\miner_daemon.pid"

if "%1"=="" (
    echo Starting LITCOIN Comprehension Mining...
    .\.venv\Scripts\python.exe litcoin_miner.py
) else if "%1"=="research" (
    echo Starting LITCOIN Research Mining...
    .\.venv\Scripts\python.exe litcoin_miner.py --research %ARG2% %ARG3% %ARG4% %ARG5%
) else if "%1"=="loop" (
    echo Starting LITCOIN Research Loop...
    .\.venv\Scripts\python.exe litcoin_miner.py --loop %ARG2% %ARG3% %ARG4% %ARG5% %ARG6%
) else if "%1"=="claim" (
    echo Claiming LITCOIN Rewards...
    .\.venv\Scripts\python.exe litcoin_miner.py --claim
) else if "%1"=="status" (
    echo Fetching Miner Status...
    .\.venv\Scripts\python.exe litcoin_miner.py --status
) else if "%1"=="mirror" (
    echo Building Dashboard Mirror Report...
    .\.venv\Scripts\python.exe dashboard_mirror.py
) else if "%1"=="bankr-mirror" (
    echo Building Bankr Mirror Report...
    .\.venv\Scripts\python.exe bankr_mirror.py
) else if "%1"=="daemon-start" (
    echo Starting Miner Daemon...
    if not exist "%RUNTIME_DIR%" mkdir "%RUNTIME_DIR%"
    for /f "usebackq delims=" %%I in (`powershell -NoProfile -Command "if (Test-Path '%PID_FILE%') { Get-Content '%PID_FILE%' }"`) do set "DAEMON_PID=%%I"
    if not "%DAEMON_PID%"=="" (
        powershell -NoProfile -Command "if (Get-Process -Id %DAEMON_PID% -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"
        if not errorlevel 1 (
            echo Daemon already running with PID %DAEMON_PID%
            goto :done
        )
    )
    if /I "%ARG2%"=="research" (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -WindowStyle Hidden -WorkingDirectory '%~dp0' -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%~dp0miner_daemon.ps1','-Mode','research' | Out-Null"
        echo Daemon start requested ^(mode=research^).
    ) else (
        powershell -NoProfile -ExecutionPolicy Bypass -Command "Start-Process -WindowStyle Hidden -WorkingDirectory '%~dp0' -FilePath 'powershell.exe' -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File','%~dp0miner_daemon.ps1' | Out-Null"
        echo Daemon start requested ^(mode=comprehension^).
    )
) else if "%1"=="daemon-stop" (
    echo Stopping Miner Daemon...
    powershell -NoProfile -Command "if (Test-Path '%PID_FILE%') { $p = Get-Content '%PID_FILE%'; Stop-Process -Id $p -Force -ErrorAction SilentlyContinue; Remove-Item '%PID_FILE%' -Force -ErrorAction SilentlyContinue; Write-Output ('Stopped PID ' + $p) } else { Write-Output 'No pid file found' }"
) else if "%1"=="daemon-status" (
    echo Checking Miner Daemon status...
    powershell -NoProfile -Command "if (Test-Path '%PID_FILE%') { $p = [int](Get-Content '%PID_FILE%'); if (Get-Process -Id $p -ErrorAction SilentlyContinue) { Write-Output ('RUNNING PID ' + $p) } else { Write-Output ('STALE PID ' + $p) } } else { Write-Output 'STOPPED' }"
) else if "%1"=="help" (
    .\.venv\Scripts\python.exe litcoin_miner.py --help
) else (
    echo Unknown command: %1
    echo.
    echo Usage:
    echo   run.bat             - Comprehension mining
    echo   run.bat research    - Research mining
    echo   run.bat loop --task=TASK_ID --rounds=50 - Iterate on task
    echo   run.bat claim       - Claim rewards
    echo   run.bat status      - Show balance
    echo   run.bat mirror      - Build dashboard mirror report
    echo   run.bat bankr-mirror - Build Bankr API+tab mirror report
    echo   run.bat daemon-start  - Start persistent daemon
    echo   run.bat daemon-stop   - Stop persistent daemon
    echo   run.bat daemon-status - Show daemon status
    echo   run.bat help        - Help
    echo.
    pause
    exit /b 1
)

:done
if "%NO_PAUSE%"=="1" goto :eof
pause
