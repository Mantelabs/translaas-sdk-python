#!/bin/bash
# Publish script for Translaas Python SDK
# This script publishes the package to PyPI or Test PyPI

set -e  # Exit on error

REPOSITORY="${1:-pypi}"  # Default to PyPI, can be 'testpypi' for Test PyPI

if [ "$REPOSITORY" != "pypi" ] && [ "$REPOSITORY" != "testpypi" ]; then
    echo "Error: Repository must be 'pypi' or 'testpypi'"
    echo "Usage: $0 [pypi|testpypi]"
    exit 1
fi

echo "Publishing Translaas Python SDK to $REPOSITORY..."

# Check if Python is available
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if distribution files exist
if [ ! -d "dist" ] || [ -z "$(ls -A dist/*.whl dist/*.tar.gz 2>/dev/null)" ]; then
    echo "Error: No distribution files found in dist/ directory"
    echo "Please run the build script first: ./scripts/build.sh"
    exit 1
fi

# Check if twine is installed
if ! python -m pip show twine &> /dev/null; then
    echo "Installing twine..."
    python -m pip install --upgrade pip
    python -m pip install twine
fi

# Check the packages before uploading
echo "Checking packages..."
python -m twine check dist/*

# Determine repository URL
if [ "$REPOSITORY" == "testpypi" ]; then
    REPO_URL="--repository-url https://test.pypi.org/legacy/"
    echo "Publishing to Test PyPI..."
else
    REPO_URL=""
    echo "Publishing to PyPI..."
fi

# Upload to PyPI
echo "Uploading packages..."
python -m twine upload $REPO_URL dist/*

echo ""
echo "✅ Publish successful!"
if [ "$REPOSITORY" == "testpypi" ]; then
    echo "📦 Package published to Test PyPI: https://test.pypi.org/project/translaas/"
else
    echo "📦 Package published to PyPI: https://pypi.org/project/translaas/"
fi
