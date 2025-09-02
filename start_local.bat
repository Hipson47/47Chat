@echo off
setlocal enabledelayedexpansion

REM 47Chat - Local run for manual testing
REM This script runs setup, then launches backend and frontend in separate terminals

REM === Config ===
set "BACKEND_HOST=127.0.0.1"
set "BACKEND_PORT=8000"

REM Move to script directory
cd /d "%~dp0"

REM Set PYTHONPATH for proper package imports
set "PYTHONPATH=%CD%"

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

REM 3) Ensure port is free before starting backend
call :free_port %BACKEND_PORT%

REM 4) Launch backend (Uvicorn) in new window
start "47Chat Backend" cmd /k ""%VENV_PY%" -m uvicorn backend.main:app --host %BACKEND_HOST% --port %BACKEND_PORT%"

REM 5) Launch frontend (Streamlit) in new window (headless to avoid auto-opening duplicate browser tabs)
start "47Chat Frontend" cmd /k ""%VENV_PY%" -m streamlit run frontend/app.py --server.port 8501 --server.address 127.0.0.1 --server.headless true"

REM 6) Open a single browser tab for the frontend (wait briefly to ensure server binds)
timeout /t 2 >nul
start "" http://localhost:8501

echo.
echo [INFO] Backend running at http://localhost:8000 (Docs: /docs)
echo [INFO] Frontend running at http://localhost:8501

echo.
echo Press any key to optionally open a tests window...
pause >nul
start "47Chat Tests" cmd /k "\"%PWSH_CMD%\" -NoProfile -ExecutionPolicy Bypass -File \"%~dp0run_tests.ps1\""

goto :eof

:free_port
rem Usage: call :free_port PORT_NUMBER
set "_PORT=%~1"

rem Use PowerShell to kill any existing Python processes that might be using the port
echo [INFO] Checking for any existing Python processes that might be using port %_PORT%...

powershell -NoProfile -Command "try { $procs = Get-Process python -ErrorAction SilentlyContinue; if ($procs) { Write-Host '[INFO] Found Python processes. Stopping them...'; $procs | Stop-Process -Force; Start-Sleep -Seconds 3; Write-Host '[INFO] Killed Python processes. Waiting completed.' } else { Write-Host '[INFO] No Python processes found, port should be free.' } } catch { Write-Host '[WARNING] Could not check/kill processes, proceeding...' }"

exit /b 0
