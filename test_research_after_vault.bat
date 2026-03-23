@echo off
REM Test script to verify research mining works after vault key is stored

echo.
echo ============================================================
echo Post-Vault-Setup Research Mining Test
echo ============================================================
echo.

REM Wait a moment for vault to finish
timeout /t 3 /nobreak

REM Check if key is in vault now
powershell -NoProfile -ExecutionPolicy Bypass -File ".\secure_vault.ps1" -Action status -Name AI_API_KEY

REM Run research mining test
echo.
echo Starting research mining test...
echo.

cmd /c "set BANKR_API_KEY=& set AI_API_KEY=& call .\run.bat research --nopause"

echo.
echo Test complete. Check diagnostics/logs for details.
pause
