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
echo "For partial commits (committing feature files, tests, or docs separately):"
echo "  Option 1: Skip specific hooks: SKIP=ruff,ruff-format git commit -m 'message'"
echo "  Option 2: Skip all hooks: git commit --no-verify -m 'message'"
echo ""
echo "Note: Hooks only run on staged files, but some checks may fail if they"
echo "require consistency across the entire codebase (e.g., imports)."
echo ""
