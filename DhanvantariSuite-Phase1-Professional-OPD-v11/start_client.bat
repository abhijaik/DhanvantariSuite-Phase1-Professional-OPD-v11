@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
) else (
    set "PY_CMD=python"
)

if "%ERP_SERVER_URL%"=="" (
    echo Note: ERP_SERVER_URL is not set.
    echo Starting desktop client in standalone local mode.
    echo To connect to a network server instead, run: set ERP_SERVER_URL=http://SERVER_IP:8000
) else (
    echo Connecting desktop client to central server: %ERP_SERVER_URL%
)

"%PY_CMD%" desktop\desktop_shell.py
endlocal


