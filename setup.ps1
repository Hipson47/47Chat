# 47Chat Setup Script (Windows PowerShell)
# Purpose: Automate environment setup for new developers on Windows.
# Actions:
# 1) Check for Python 3.10+ in PATH
# 2) Create virtual environment at .venv
# 3) Install dependencies from backend/requirements.txt
# 4) Check Ollama service; guide installation and attempt "ollama pull llama3"
# 5) Create .env from .env.example and prompt for OPENAI_API_KEY
# 6) Print instructions to run backend and frontend

$ErrorActionPreference = 'Stop'

Write-Host "=== 47Chat Setup (Windows) ===" -ForegroundColor Cyan

function Test-Python310 {
  param(
    [ref]$PythonCmd
  )
  try {
    $out = & python --version 2>&1
    if ($LASTEXITCODE -eq 0 -and $out) {
      $versionString = ($out | Select-Object -First 1) -replace 'Python\s+', ''
      try { $ver = [version]$versionString } catch { $ver = $null }
      if ($ver -and ($ver.Major -gt 3 -or ($ver.Major -eq 3 -and $ver.Minor -ge 10))) {
        $PythonCmd.Value = 'python'
        return $true
      }
    }
  } catch { }

  try {
    $out = & py -3.10 -V 2>&1
    if ($LASTEXITCODE -eq 0 -and $out) {
      $versionString = ($out | Select-Object -First 1) -replace 'Python\s+', ''
      try { $ver = [version]$versionString } catch { $ver = $null }
      if ($ver -and ($ver.Major -eq 3 -and $ver.Minor -ge 10)) {
        $PythonCmd.Value = 'py -3.10'
        return $true
      }
    }
  } catch { }

  return $false
}

# 1) Check Python 3.10+
$pythonCmdRef = ''
if (-not (Test-Python310 -PythonCmd ([ref]$pythonCmdRef))) {
  Write-Error "Python 3.10+ not found in PATH. Install Python 3.10 or newer from https://www.python.org/downloads/ and re-run this script."
  exit 1
}
$pythonCmd = $pythonCmdRef
Write-Host "Using Python command: $pythonCmd" -ForegroundColor Green

# 2) Create virtual environment
if (-not (Test-Path '.venv')) {
  Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Yellow
  & $pythonCmd -m venv .venv
} else {
  Write-Host ".venv already exists. Skipping creation." -ForegroundColor DarkYellow
}

# 3) Install dependencies
# Resolve venv python executable reliably
$venvPython = Join-Path (Get-Location) ".venv\\Scripts\\python.exe"
if (-not (Test-Path $venvPython)) { $venvPython = ".venv/Scripts/python.exe" }

Write-Host "Upgrading pip and installing dependencies from backend/requirements.txt..." -ForegroundColor Yellow
& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install -r backend/requirements.txt

# 4) Check Ollama service
function Test-Ollama {
  try {
    $resp = Invoke-WebRequest -Uri 'http://localhost:11434/api/tags' -UseBasicParsing -TimeoutSec 5
    return ($resp.StatusCode -eq 200)
  } catch { return $false }
}

if (Test-Ollama) {
  Write-Host "Ollama service is reachable at http://localhost:11434" -ForegroundColor Green
} else {
  Write-Warning "Ollama service not reachable. Install from https://ollama.com and ensure the service is running."
  if (Get-Command ollama -ErrorAction SilentlyContinue) {
    try {
      Write-Host "Attempting to pull llama3 model with 'ollama pull llama3'..." -ForegroundColor Yellow
      ollama pull llama3
    } catch {
      Write-Warning "Could not pull model automatically. Please run 'ollama pull llama3' after installing Ollama."
    }
  } else {
    Write-Warning "'ollama' CLI not found. After installation, run 'ollama serve' and 'ollama pull llama3'."
  }
}

# 5) Create .env from .env.example and prompt for OPENAI_API_KEY
$envExample = @(
  "# 47Chat environment variables",
  "# Provide your OpenAI API key used by the moderator agent (optional)",
  "OPENAI_API_KEY=",
  "",
  "# Optional overrides",
  "# OLLAMA_MODEL=llama3"
)

Set-Content -Path '.env.example' -Value $envExample -Encoding UTF8
Write-Host "Refreshed .env.example" -ForegroundColor Green

if (-not (Test-Path '.env')) {
  Copy-Item '.env.example' '.env'
  Write-Host "Created .env from template (.env.example)" -ForegroundColor Green
}

# Prompt user to set OPENAI_API_KEY
try {
  $currentEnv = Get-Content '.env' -ErrorAction Stop
} catch { $currentEnv = @() }

$needsKey = $true
foreach ($line in $currentEnv) {
  if ($line -match '^OPENAI_API_KEY=') {
    $value = $line.Substring('OPENAI_API_KEY='.Length)
    if ($value -and $value.Trim().Length -gt 0) { $needsKey = $false }
  }
}

if ($needsKey) {
  $key = Read-Host "Enter your OPENAI_API_KEY (press Enter to skip)"
  if ($key) {
    $updated = @()
    $replaced = $false
    foreach ($line in $currentEnv) {
      if ($line -match '^OPENAI_API_KEY=') {
        $updated += "OPENAI_API_KEY=$key"
        $replaced = $true
      } else {
        $updated += $line
      }
    }
    if (-not $replaced) { $updated += "OPENAI_API_KEY=$key" }
    Set-Content '.env' -Value $updated -Encoding UTF8
    $env:OPENAI_API_KEY = $key
    Write-Host "Saved OPENAI_API_KEY to .env and set in current session." -ForegroundColor Green
  } else {
    Write-Warning "OPENAI_API_KEY not set. OpenAI-based moderation will use mock responses until you set it."
  }
}

Write-Host "" 
Write-Host "=== Setup Complete ===" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1) (Optional) Allow script activation if needed: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned" -ForegroundColor DarkGray
Write-Host "2) Activate virtual env: .\\.venv\\Scripts\\Activate.ps1" -ForegroundColor Green
Write-Host "3) Start backend: uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000" -ForegroundColor Green
Write-Host "4) Start frontend (new terminal): streamlit run frontend/app.py" -ForegroundColor Green
Write-Host "5) Open UI: http://localhost:8501 | API: http://localhost:8000/docs" -ForegroundColor Green
