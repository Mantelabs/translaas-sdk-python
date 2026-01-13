# Wrapper script for pytest that allows exit code 5 (no tests collected)
# This prevents blocking pushes during initial project setup

pytest
$exitCode = $LASTEXITCODE

# Exit code 5 means no tests were collected, which is OK during initial setup
if ($exitCode -eq 5) {
    Write-Host "No tests collected - this is OK during initial setup" -ForegroundColor Yellow
    exit 0
}

# Any other exit code should fail the hook
exit $exitCode
