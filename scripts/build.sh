#!/bin/bash
# Build script for Translaas Python SDK
# This script builds the package distribution files (wheel and source distribution)

set -e  # Exit on error

echo "Building Translaas Python SDK..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if build tool is installed
if ! python -m pip show build &> /dev/null; then
    echo "Installing build dependencies..."
    python -m pip install --upgrade pip
    python -m pip install build
fi

# Clean previous builds
echo "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Build the package
echo "Building package..."
python -m build

# Check the built packages
echo "Checking built packages..."
python -m pip install twine --quiet
python -m twine check dist/*

echo ""
echo "✅ Build successful!"
echo "📦 Distribution files are in the 'dist/' directory:"
ls -lh dist/
