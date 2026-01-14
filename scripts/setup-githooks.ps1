# Setup script for git hooks using pre-commit framework (PowerShell)

$ErrorActionPreference = "Stop"

Write-Host "Setting up git hooks for Translaas SDK..." -ForegroundColor Cyan

# Check if pre-commit is installed
try {
    $null = Get-Command pre-commit -ErrorAction Stop
    Write-Host "pre-commit is already installed." -ForegroundColor Yellow
} catch {
    Write-Host "pre-commit is not installed. Installing..." -ForegroundColor Yellow
    pip install pre-commit
}

# Install hooks
Write-Host "Installing pre-commit hooks..." -ForegroundColor Yellow
pre-commit install --hook-type pre-commit --hook-type pre-push

Write-Host ""
Write-Host "✅ Git hooks setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "Hooks configured:" -ForegroundColor Cyan
Write-Host "  - pre-commit: Runs ruff linting/formatting and mypy type checking on staged files" -ForegroundColor White
Write-Host "  - pre-push: Runs pytest before pushing" -ForegroundColor White
Write-Host ""
Write-Host "To test the hooks manually:" -ForegroundColor Cyan
Write-Host "  pre-commit run --all-files" -ForegroundColor White
Write-Host ""
Write-Host "To skip hooks (use with caution):" -ForegroundColor Cyan
Write-Host "  git commit --no-verify" -ForegroundColor White
Write-Host "  git push --no-verify" -ForegroundColor White
Write-Host ""
Write-Host "For partial commits (committing feature files, tests, or docs separately):" -ForegroundColor Cyan
Write-Host "  Option 1: Skip specific hooks: `$env:SKIP='ruff,ruff-format'; git commit -m 'message'" -ForegroundColor White
Write-Host "  Option 2: Skip all hooks: git commit --no-verify -m 'message'" -ForegroundColor White
Write-Host ""
Write-Host "Note: Hooks only run on staged files, but some checks may fail if they" -ForegroundColor Yellow
Write-Host "require consistency across the entire codebase (e.g., imports)." -ForegroundColor Yellow
Write-Host ""
