# Runs the project's tests using pytest from the backend directory
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Push-Location backend
try {
  python -m pytest
} finally {
  Pop-Location
}
