# Build script for Translaas Python SDK
# This script builds the package distribution files (wheel and source distribution)

$ErrorActionPreference = "Stop"

Write-Host "Building Translaas Python SDK..." -ForegroundColor Cyan

# Check if Python is available
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    exit 1
}

# Check if build tool is installed
$buildInstalled = python -m pip show build 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing build dependencies..." -ForegroundColor Yellow
    python -m pip install --upgrade pip
    python -m pip install build
}

# Clean previous builds
Write-Host "Cleaning previous builds..." -ForegroundColor Yellow
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
Get-ChildItem -Filter "*.egg-info" -Directory | Remove-Item -Recurse -Force

# Build the package
Write-Host "Building package..." -ForegroundColor Yellow
python -m build

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Build failed" -ForegroundColor Red
    exit 1
}

# Check the built packages
Write-Host "Checking built packages..." -ForegroundColor Yellow
python -m pip install twine --quiet
python -m twine check dist/*

if ($LASTEXITCODE -ne 0) {
    Write-Host "Error: Package check failed" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "✅ Build successful!" -ForegroundColor Green
Write-Host "📦 Distribution files are in the 'dist/' directory:" -ForegroundColor Cyan
Get-ChildItem dist/ | Format-Table Name, Length, LastWriteTime
