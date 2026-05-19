# Create model-tests/.venv with Python 3.13.4 and install dependencies.
$ErrorActionPreference = "Stop"
$ModelTestsRoot = Split-Path -Parent $PSScriptRoot
$VenvPython = Join-Path $ModelTestsRoot ".venv\Scripts\python.exe"
$DefaultPython = "C:\Users\marce\tech\python3.13.4\python.exe"

$BasePython = if ($env:MODEL_TESTS_PYTHON) { $env:MODEL_TESTS_PYTHON } else { $DefaultPython }
if (-not (Test-Path $BasePython)) {
    Write-Error "Python not found at $BasePython. Set MODEL_TESTS_PYTHON to your python.exe path."
}

if (-not (Test-Path $VenvPython)) {
    Write-Host "Creating venv at $ModelTestsRoot\.venv ..."
    & $BasePython -m venv (Join-Path $ModelTestsRoot ".venv")
}

Write-Host "Installing requirements ..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r (Join-Path $ModelTestsRoot "requirements.txt")

Write-Host "Done. Activate with:"
Write-Host "  $($ModelTestsRoot)\.venv\Scripts\Activate.ps1"
Write-Host "Or run comparisons via scripts\run.ps1"
