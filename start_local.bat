@echo off
setlocal enabledelayedexpansion

REM 47Chat - Local run for manual testing
REM This script runs setup, then launches backend and frontend in separate terminals

REM Move to script directory
cd /d "%~dp0"

REM Locate PowerShell (Windows PowerShell or PowerShell 7)
set "PWSH_CMD=%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe"
if not exist "%PWSH_CMD%" (
  for /f "delims=" %%I in ('where pwsh 2^>nul') do set "PWSH_CMD=%%I"
)
if not exist "%PWSH_CMD%" (
  for /f "delims=" %%I in ('where powershell 2^>nul') do set "PWSH_CMD=%%I"
)
if not exist "%PWSH_CMD%" (
  echo [ERROR] PowerShell not found in PATH. Please install PowerShell or run setup.ps1 manually.
  echo Try: C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -NoProfile -ExecutionPolicy Bypass -File setup.ps1
  pause
  exit /b 1
)

REM 1) Run setup (creates .venv, installs deps, optional Ollama setup)
"%PWSH_CMD%" -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 (
  echo [ERROR] Setup failed. Fix issues and re-run.
  pause
  exit /b 1
)

REM 2) Resolve venv python
set "VENV_PY=%~dp0.venv\Scripts\python.exe"
if not exist "%VENV_PY%" (
  echo [ERROR] Virtual env Python not found at "%VENV_PY%".
  echo Please run setup.ps1 manually and retry.
  pause
  exit /b 1
)

REM 3) Launch backend (Uvicorn) in new window
start "47Chat Backend" cmd /k ""%VENV_PY%" -m uvicorn backend.main:app --host 127.0.0.1 --port 8000"

REM 4) Launch frontend (Streamlit) in new window (headless to avoid auto-opening duplicate browser tabs)
start "47Chat Frontend" cmd /k ""%VENV_PY%" -m streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true"

REM 5) Open a single browser tab for the frontend (wait briefly to ensure server binds)
timeout /t 2 >nul
start "" http://localhost:8501

echo.
echo [INFO] Backend running at http://localhost:8000 (Docs: /docs)
echo [INFO] Frontend running at http://localhost:8501

echo.
echo Press any key to optionally open a tests window...
pause >nul
start "47Chat Tests" cmd /k "\"%PWSH_CMD%\" -NoProfile -ExecutionPolicy Bypass -File \"%~dp0run_tests.ps1\""

exit /b 0
