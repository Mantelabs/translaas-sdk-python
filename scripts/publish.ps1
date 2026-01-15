# Publish script for Translaas Python SDK
# This script publishes the package to PyPI or Test PyPI

param(
    [Parameter(Position=0)]
    [ValidateSet("pypi", "testpypi")]
    [string]$Repository = "pypi"
)

$ErrorActionPreference = "Stop"

Write-Host "Publishing Translaas Python SDK to $Repository..." -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if distribution files exist
if (-not (Test-Path "dist")) {
    Write-Host "Error: No dist/ directory found" -ForegroundColor Red
    Write-Host "Please run the build script first: .\scripts\build.ps1" -ForegroundColor Yellow
    exit 1
}

$distFiles = Get-ChildItem dist/*.whl, dist/*.tar.gz -ErrorAction SilentlyContinue
if (-not $distFiles) {
    Write-Host "Error: No distribution files found in dist/ directory" -ForegroundColor Red
    Write-Host "Please run the build script first: .\scripts\build.ps1" -ForegroundColor Yellow
    exit 1
}

# Check if twine is installed
$twineInstalled = python -m pip show twine 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing twine..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install twine
}

# Check the packages before uploading
Write-Host "Checking packages..." -ForegroundColor Yellow
python -m twine check dist/*

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Package check failed" -ForegroundColor Red
    exit 1
}

# Determine repository URL
$repoUrl = ""
if ($Repository -eq "testpypi") {
    $repoUrl = "--repository-url https://test.pypi.org/legacy/"
    Write-Host "Publishing to Test PyPI..." -ForegroundColor Yellow
} else {
    Write-Host "Publishing to PyPI..." -ForegroundColor Yellow
}

# Upload to PyPI
Write-Host "Uploading packages..." -ForegroundColor Yellow
if ($repoUrl) {
    python -m twine upload $repoUrl dist/*
} else {
    python -m twine upload dist/*
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Upload failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Publish successful!" -ForegroundColor Green
if ($Repository -eq "testpypi") {
    Write-Host "📦 Package published to Test PyPI: https://test.pypi.org/project/translaas/" -ForegroundColor Cyan
} else {
    Write-Host "📦 Package published to PyPI: https://pypi.org/project/translaas/" -ForegroundColor Cyan
}
