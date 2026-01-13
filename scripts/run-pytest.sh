#!/bin/bash
# Wrapper script for pytest that allows exit code 5 (no tests collected)
# This prevents blocking pushes during initial project setup

pytest
exit_code=$?

# Exit code 5 means no tests were collected, which is OK during initial setup
if [ $exit_code -eq 5 ]; then
    echo "No tests collected - this is OK during initial setup"
    exit 0
fi

# Any other exit code should fail the hook
exit $exit_code
