#!/bin/bash
# Setup script for git hooks using pre-commit framework

set -e

echo "Setting up git hooks for Translaas SDK..."

# Check if pre-commit is installed
if ! command -v pre-commit &> /dev/null; then
    echo "pre-commit is not installed. Installing..."
    pip install pre-commit
else
    echo "pre-commit is already installed."
fi

# Install hooks
echo "Installing pre-commit hooks..."
pre-commit install --hook-type pre-commit --hook-type pre-push

echo ""
echo "✅ Git hooks setup complete!"
echo ""
echo "Hooks configured:"
echo "  - pre-commit: Runs ruff linting/formatting and mypy type checking on staged files"
echo "  - pre-push: Runs pytest before pushing"
echo ""
echo "To test the hooks manually:"
echo "  pre-commit run --all-files"
echo ""
echo "To skip hooks (use with caution):"
echo "  git commit --no-verify"
echo "  git push --no-verify"
echo ""
