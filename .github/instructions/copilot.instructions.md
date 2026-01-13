# Translaas SDK - Copilot Instructions

## Repository Overview

This is an open-source Python SDK for the Translaas Translation Delivery API SaaS. The SDK provides a strongly-typed, performant, and modular way to consume translation APIs in Python applications. The backend API is proprietary, but this SDK is open-sourced to allow community contributions.

**Repository Type**: Python SDK library  
**Languages**: Python  
**Python Versions**: Python 3.8+  
**Build System**: setuptools / pyproject.toml (PEP 518)  
**Test Framework**: pytest  
**Package Management**: pip / pyproject.toml

## High-Level Architecture

The SDK is organized into modular packages:

- **translaas.models** (`translaas/models/`) - Data transfer objects (DTOs) only, minimal dependencies
- **translaas.client** (`translaas/client/`) - Core HTTP client implementation
- **translaas.caching** (`translaas/caching/`) - Caching abstractions and implementations
- **translaas.caching_file** (`translaas/caching_file/`) - File-based caching
- **translaas.extensions** (`translaas/extensions/`) - Framework integrations (Flask, FastAPI, Django)

Each source module has corresponding tests in `tests/` directory following the naming pattern `test_*.py`.

## Build and Validation Instructions

### Prerequisites

- Python 3.8 or later (required for building and testing)
- pip (Python package installer)
- virtualenv or venv (for isolated environments)

### Setup Virtual Environment

**Always use a virtual environment:**

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Install Dependencies

**Install package in development mode:**

```bash
pip install -e ".[dev]"
```

This installs the package in editable mode with development dependencies (pytest, mypy, ruff, etc.).

**Install dependencies from requirements files:**

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

### Build

**Build source distribution:**

```bash
python -m build
```

**Build wheel:**

```bash
python -m build --wheel
```

**Build both:**

```bash
python -m build
```

This creates distribution packages in `dist/` directory.

**Important**: The package configuration is in `pyproject.toml`. Use `python -m build` from the root directory.

### Test

**Run all tests:**

```bash
pytest
```

**Run tests for specific module:**

```bash
pytest tests/test_client.py
```

**Run tests with coverage:**

```bash
pytest --cov=translaas --cov-report=html
```

**Run tests with verbose output:**

```bash
pytest -v
```

**Run tests matching pattern:**

```bash
pytest -k "test_get_entry"
```

**Run tests without building (faster after install):**

```bash
pytest --no-cov
```

**Important**: Tests must pass for all supported Python versions. Always run `pytest` before committing changes.

### Type Checking

**Run mypy:**

```bash
mypy translaas/
```

**Run pyright:**

```bash
pyright translaas/
```

### Linting

**Run ruff:**

```bash
ruff check .
```

**Run ruff with auto-fix:**

```bash
ruff check --fix .
```

**Run black (formatting):**

```bash
black translaas/ tests/
```

### Validation Steps

**Before committing, always:**

1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -e ".[dev]"`
3. Run type checking: `mypy translaas/`
4. Run linting: `ruff check .`
5. Run all tests: `pytest`
6. Verify tests pass with coverage: `pytest --cov=translaas`

**CI Pipeline Validation:**

The CI pipeline (`.github/workflows/ci.yml`) runs:
- Install dependencies: `pip install -e ".[dev]"`
- Type checking: `mypy translaas/`
- Linting: `ruff check .`
- Testing with coverage: `pytest --cov=translaas --cov-report=xml`

**Note**: CI tests on Python 3.8, 3.9, 3.10, 3.11, 3.12 (matrix strategy).

## Project Layout and File Management

### Critical File Synchronization Rules

**CRITICAL**: When files are added or removed, ensure:
- Package includes are updated in `pyproject.toml` (`[tool.setuptools.packages.find]` or `packages` field)
- Dependencies are correctly listed in `pyproject.toml` (`[project.dependencies]` or `install_requires`)
- Exports are updated in `__init__.py` files if adding new public APIs
- Test files follow naming convention `test_*.py`

**When creating a new module:**
- Python files (`.py`) are automatically included if in package directories
- Ensure `__init__.py` files exist in package directories
- Add module to appropriate `__init__.py` exports if it's part of public API

**When creating a new package:**
- Create directory with `__init__.py` file
- Update `pyproject.toml` if needed for package discovery
- Create corresponding test files in `tests/` directory

**When removing a module:**
- Remove from `__init__.py` exports if it was exported
- Remove corresponding test files

### Directory Structure

```
translaas-sdk-python/
├── .github/
│   ├── workflows/
│   │   └── ci.yml                    # CI/CD pipeline
│   └── instructions/
│       └── copilot.instructions.md   # This file
├── translaas/                        # Source package
│   ├── __init__.py
│   ├── models/                      # DTOs and models
│   │   ├── __init__.py
│   │   └── models.py
│   ├── client/                      # HTTP client
│   │   ├── __init__.py
│   │   └── client.py
│   ├── caching/                     # Caching layer
│   │   ├── __init__.py
│   │   └── cache.py
│   ├── caching_file/                # File-based caching
│   │   ├── __init__.py
│   │   └── file_cache.py
│   ├── extensions/                  # Framework integrations
│   │   ├── __init__.py
│   │   ├── flask.py
│   │   ├── fastapi.py
│   │   └── django.py
│   └── exceptions.py                # Exception classes
├── tests/                           # Test files
│   ├── __init__.py
│   ├── test_client.py
│   ├── test_cache.py
│   └── test_models.py
├── pyproject.toml                   # Build configuration (PEP 518)
├── setup.py                         # Setuptools configuration (if needed)
├── setup.cfg                         # Additional configuration
├── requirements.txt                  # Runtime dependencies
├── requirements-dev.txt              # Development dependencies
├── README.md                         # Project documentation
├── CONTRIBUTING.md                   # Contribution guidelines
└── LICENSE                           # MIT License
```

### Key Configuration Files

- **pyproject.toml**: Build configuration, dependencies, tool configurations (PEP 518)
- **setup.py**: Setuptools configuration (if using legacy setup.py)
- **setup.cfg**: Additional setuptools configuration
- **requirements.txt**: Runtime dependencies (optional, can use pyproject.toml)
- **requirements-dev.txt**: Development dependencies (optional)
- **.github/workflows/ci.yml**: CI/CD pipeline configuration
- **.cursor/rules/translaas-sdk-rules.mdc**: Comprehensive development rules and guidelines

## Development Guidelines

### Test-Driven Development (TDD) - MANDATORY

**TDD is mandatory for all code changes.** Follow the Red-Green-Refactor cycle:

1. **Red**: Write a failing test that describes the desired behavior
2. **Green**: Write the minimum code necessary to make the test pass
3. **Refactor**: Improve the code while keeping tests green

**Rules:**
- Write tests BEFORE implementation
- Every module MUST have corresponding tests in `tests/`
- Test file naming: `test_*.py`
- Test function naming: `test_{method_name}_{scenario}_{expected_behavior}`
- All public APIs must have tests
- Test both success and failure scenarios

### Code Style

- Follow **PEP 8** style guide strictly
- Use `async`/`await` for all I/O operations
- Use type hints (`typing` module) for all function signatures
- Use `Optional[T]` or `T | None` (Python 3.10+) for nullable types
- Use `dataclasses` or `TypedDict` for structured data
- Use `Enum` for constants with named values
- Use `f-strings` for string formatting
- All public APIs require docstrings (Google or NumPy style)

### Python Version Support

- Code must work with Python 3.8+
- Use `typing_extensions` for features not available in older Python versions
- Test code against all supported Python versions when possible
- Use `python_requires` in `pyproject.toml` to specify minimum version

### Dependencies

- **Never** add dependencies without strong justification
- Prefer standard library modules over third-party libraries
- Use `httpx` for async HTTP (preferred) or `requests` for sync HTTP
- Use `pydantic` for runtime validation if needed (optional dependency)
- Keep Models package dependency-free
- All package versions managed in `pyproject.toml` or `requirements.txt`

### Error Handling

- Use custom exceptions: `TranslaasException`, `TranslaasApiException`, `TranslaasConfigurationException`
- Support cancellation tokens (`asyncio.CancelledError` or custom cancellation) in async methods
- Handle HTTP status codes appropriately
- Include helpful error messages

## Common Commands Reference

**Setup and install:**
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

**Build and test:**
```bash
python -m build && pytest
```

**Clean and rebuild:**
```bash
rm -rf dist/ build/ *.egg-info/
python -m build
```

**Run all checks:**
```bash
mypy translaas/ && ruff check . && pytest
```

**Create new test file:**
```bash
touch tests/test_new_feature.py
```

## Pre-Commit Checklist

Before committing code, verify:

- [ ] TDD followed - Tests written before implementation
- [ ] Test file created (if adding new module)
- [ ] All tests pass: `pytest`
- [ ] Type checking passes: `mypy translaas/`
- [ ] Linting passes: `ruff check .`
- [ ] Package builds: `python -m build`
- [ ] Docstrings added for public APIs
- [ ] Code follows PEP 8 conventions
- [ ] No unnecessary dependencies added
- [ ] Python version compatibility verified (3.8+)

## Trust Instructions

**Trust these instructions** - they have been validated and tested. Only search the codebase if:
- Information in these instructions is incomplete
- Instructions are found to be in error
- A specific file or implementation detail is needed

The instructions above represent the validated, working state of the repository. Use them as the primary source of truth for build, test, and development workflows.
