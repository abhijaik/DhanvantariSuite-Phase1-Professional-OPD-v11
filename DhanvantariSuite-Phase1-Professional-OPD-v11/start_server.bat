@echo off
setlocal
cd /d "%~dp0"
if "%DATABASE_URL%"=="" set DATABASE_URL=postgresql://postgres:password@localhost:5432/clinic_erp

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

echo Starting Dhanvantari Clinic ERP Server...
echo Database: %DATABASE_URL%
"%PY_CMD%" src\server.py %*
endlocal

