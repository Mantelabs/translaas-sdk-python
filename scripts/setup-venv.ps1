# Setup script for creating a virtual environment and installing dependencies (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Setting up Translaas SDK development environment..." -ForegroundColor Cyan

# Create virtual environment
if (-not (Test-Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
} else {
    Write-Host "Virtual environment already exists." -ForegroundColor Yellow
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& "venv\Scripts\Activate.ps1"

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install package in development mode with dev dependencies
Write-Host "Installing package in development mode..." -ForegroundColor Yellow
pip install -e ".[dev]"

# Verify installation
Write-Host "Verifying installation..." -ForegroundColor Yellow
python -c "import translaas; print(f'Translaas SDK version: {translaas.__version__}')"

Write-Host ""
Write-Host "✅ Development environment setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To activate the virtual environment in the future, run:" -ForegroundColor Cyan
Write-Host "  .\venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host ""
Write-Host "To run tests:" -ForegroundColor Cyan
Write-Host "  pytest" -ForegroundColor White
Write-Host ""
Write-Host "To build the package:" -ForegroundColor Cyan
Write-Host "  python -m build" -ForegroundColor White
Write-Host ""
