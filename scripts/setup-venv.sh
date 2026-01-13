#!/bin/bash
# Setup script for creating a virtual environment and installing dependencies

set -e

echo "Setting up Translaas SDK development environment..."

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install package in development mode with dev dependencies
echo "Installing package in development mode..."
pip install -e ".[dev]"

# Verify installation
echo "Verifying installation..."
python -c "import translaas; print(f'Translaas SDK version: {translaas.__version__}')"

echo ""
echo "✅ Development environment setup complete!"
echo ""
echo "To activate the virtual environment in the future, run:"
echo "  source venv/bin/activate"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To build the package:"
echo "  python -m build"
echo ""
