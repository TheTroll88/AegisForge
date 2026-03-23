@echo off
echo ============================================================
echo  Screenshot OCR Pipeline
echo ============================================================
echo.

cd /d "%~dp0"
call .venv\Scripts\activate.bat

echo Running pipeline...
echo.
python ocr_pipeline.py %*

echo.
echo ============================================================
echo  Done. Check D:\DataVault\Logs for outputs.
echo ============================================================
pause
