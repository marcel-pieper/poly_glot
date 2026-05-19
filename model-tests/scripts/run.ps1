# Run compare_models.py using model-tests/.venv
$ErrorActionPreference = "Stop"
$ModelTestsRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ModelTestsRoot ".venv\Scripts\python.exe"

if (-not (Test-Path $VenvPython)) {
    Write-Host "Venv not found. Running setup ..."
    & (Join-Path $PSScriptRoot "setup.ps1")
}

$CompareScript = Join-Path $ModelTestsRoot "compare_models.py"
& $VenvPython $CompareScript @args
