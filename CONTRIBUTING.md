# Contributing to Translaas SDK

We welcome contributions to the Translaas SDK! This document provides guidelines and instructions for contributing.

## Getting Started

1. **Fork the repository** and clone your fork locally
2. **Create a branch** for your feature or bug fix:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

3. **Set up your development environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e ".[dev]"
   python -m build
   ```

## Development Guidelines

### Code Style

- Follow **PEP 8** style guide strictly
- Use meaningful variable and method names (snake_case for functions/variables, PascalCase for classes)
- Add docstrings for public APIs (Google or NumPy style)
- Keep functions focused and single-purpose
- Use `async`/`await` for asynchronous operations
- Use type hints (`typing` module) for all function signatures
- Use `ruff` and `black` for code formatting (configured in the project)

### Optional: Auto-format on commit (pre-commit hook)

This repo includes an **opt-in** git hooks setup using the `pre-commit` framework that will:

**Pre-commit hooks (run before each commit):**
- Run `ruff` linting with auto-fix on **staged files**
- Run `ruff-format` (black-compatible formatter) on **staged files**
- Check for trailing whitespace, end-of-file issues
- Validate YAML, TOML, and JSON files
- Check for merge conflicts and debug statements
- **Note:** `mypy` type checking is disabled in pre-commit (can be slow) - run manually: `mypy translaas/`

**Pre-push hooks (run before each push):**
- Run `pytest` to ensure all tests pass

Enable it once per clone:

```bash
# Linux/macOS
./scripts/setup-githooks.sh

# Windows (PowerShell)
pwsh -NoProfile -ExecutionPolicy Bypass -File scripts/setup-githooks.ps1

# Or manually:
pip install -e ".[dev]"
pre-commit install --hook-type pre-commit --hook-type pre-push
```

**Note:** Hooks can be skipped if needed using `git commit --no-verify` or `git push --no-verify`, but this should be used sparingly.

### Package Structure

- Keep code organized within the appropriate module:
  - `translaas.models` - Data transfer objects only
  - `translaas.client` - Core HTTP client implementation
  - `translaas.caching` - In-memory caching layer
  - `translaas.caching_file` - File-based offline caching with hybrid caching support
  - `translaas.extensions` - Framework integrations and extensions

#### Test File Structure

All test files should be placed in the `tests/` directory:

```
translaas/
├── translaas/
│   ├── __init__.py
│   ├── client.py
│   └── cache.py
├── tests/
│   ├── __init__.py
│   ├── test_client.py
│   └── test_cache.py
└── pyproject.toml
```

Each test file should:
- Be named `test_*.py` (e.g., `test_client.py`)
- Use `pytest` as the testing framework
- Include proper mocking for external dependencies
- Use descriptive test names following the pattern: `test_{method_name}_{scenario}_{expected_behavior}`

### Multi-Environment Support

The Translaas SDK is configured to work in multiple Python environments:
- **Python 3.8+** - CPython and PyPy support
- **AsyncIO** - Full async/await support
- **Standard Library** - Prefer standard library over third-party dependencies

#### pyproject.toml Configuration

The `pyproject.toml` file should include:

```toml
[project]
name = "translaas"
version = "1.0.0"
requires-python = ">=3.8"
dependencies = [
    "httpx>=0.24.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "mypy>=1.0.0",
    "ruff>=0.1.0",
    "black>=23.0.0",
]
```

#### Key Points

1. **Python Modules**: Use standard Python modules (`import`/`from`)
2. **Type Hints**: All source code should include type hints
3. **Build Output**: Package builds to `dist/` directory
4. **Type Checking**: Use `mypy` or `pyright` for static type checking

#### Environment Compatibility

When writing code, be aware of environment differences:

- **Python 3.8+**:
  - Full async/await support
  - Type hints available
  - Use `typing_extensions` for features not in older Python versions

- **AsyncIO**:
  - Use `asyncio` for async operations
  - Use `httpx` for async HTTP requests
  - Support cancellation tokens

#### Conditional Code

If you need version-specific code:

```python
import sys
from typing import TYPE_CHECKING

# Runtime check (preferred)
if sys.version_info >= (3, 10):
    # Python 3.10+ code
    from typing import TypeAlias
else:
    # Python 3.8-3.9 code
    from typing_extensions import TypeAlias

# Type checking only
if TYPE_CHECKING:
    from typing import Protocol
```

### Test-Driven Development (TDD)

We follow **Test-Driven Development (TDD)** practices. This means:

1. **Write tests first** - Before implementing any feature, write a failing test
2. **Make it pass** - Write the minimum code to make the test pass
3. **Refactor** - Improve the code while keeping tests green

#### TDD Workflow

```
Red → Green → Refactor
```

- **Red**: Write a failing test that describes the desired behavior
- **Green**: Write the minimum code to make the test pass
- **Refactor**: Improve code quality while keeping tests passing

### Testing

- **Follow TDD** - Write tests before implementation
- **Every module must have tests** - Test files are located in `tests/` directory
- **Test file naming**: `test_*.py` (e.g., `test_client.py`)
- Write unit tests for all public APIs
- Test both success and failure scenarios
- Ensure all tests pass before submitting a pull request
- Maintain or improve code coverage (aim for 80%+)
- Test against all supported Python versions when possible
- Use proper test naming: `test_{method_name}_{scenario}_{expected_behavior}`

### Dependencies

- Minimize external dependencies
- Use standard library modules when possible (e.g., `json`, `asyncio`, `typing`)
- Prefer built-in Python APIs over third-party libraries
- Document any new dependencies and their justification
- Use type stubs (`types-*` packages) for third-party libraries without type hints

## Pull Request Process

1. **Follow TDD workflow**:
   - Write failing tests first (Red)
   - Implement code to make tests pass (Green)
   - Refactor while keeping tests green
2. **Create test file** if adding a new module:
   - Create test file in `tests/` directory
   - Name it `test_{module_name}.py`
   - Add appropriate test dependencies (pytest, pytest-asyncio, pytest-mock)
3. **Update version** if your changes should be versioned:
   - Update version in `pyproject.toml` or `__version__` in `__init__.py`
   - Follow Semantic Versioning (SemVer)
   - Document changes in CHANGELOG.md
4. **Update documentation** if you're adding features or changing behavior
5. **Ensure test coverage**:
   - All public APIs have tests
   - Both success and failure scenarios are tested
   - Tests follow naming convention: `test_{method_name}_{scenario}_{expected_behavior}`
6. **Run the build** to ensure everything builds:
   ```bash
   python -m build
   ```
7. **Run type checking** to ensure type hints are correct:
   ```bash
   mypy translaas/
   ```
8. **Run tests** and ensure all pass:
   ```bash
   pytest
   ```
9. **Run linting** to ensure code style is correct:
   ```bash
   ruff check .
   ```
10. **Format code** to ensure consistent formatting:
    ```bash
    black translaas/ tests/
    ```
11. **Update the README** if you're adding new features or changing usage
12. **Write a clear PR description**:
    - What changes were made
    - Why the changes were made
    - How to test the changes
    - Any breaking changes
    - Test coverage information

## Commit Messages

Use clear, descriptive commit messages following conventional commits:

```
feat: Add support for custom cache providers
fix: Resolve timeout issue in retry policy
docs: Update README with caching examples
refactor: Simplify HTTP client configuration
test: Add unit tests for retry policy
chore: Update dependencies
```

### Commit Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation only changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependency updates, etc.
- `build`: Build system changes
- `ci`: CI/CD changes

## Reporting Issues

When reporting bugs or requesting features:

- Use the GitHub issue tracker
- Provide a clear description of the issue
- Include steps to reproduce (for bugs)
- Specify the Python version and environment you're using
- Include relevant code samples or error messages
- Use appropriate labels if you have permission

### Issue Templates

When creating an issue, please use the appropriate template:
- **Bug Report**: For reporting bugs
- **Feature Request**: For requesting new features
- **Question**: For asking questions about usage or implementation

## Code Review Process

1. All pull requests require at least one approval
2. Ensure CI/CD checks pass
3. Address review feedback promptly
4. Keep pull requests focused and reasonably sized
5. Rebase on main branch if requested

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers and help them get started
- Focus on constructive feedback
- Respect different viewpoints and experiences
- Be patient with questions and learning curves

## Questions?

If you have questions about contributing, please:
- Open an issue with the `question` label
- Check existing issues and discussions
- Review the codebase to understand patterns and conventions

## Testing Resources

### Creating a Test File

To create a new test file:

```bash
# Navigate to tests directory
cd tests

# Create test file
touch test_my_module.py
```

### Example Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch
from translaas.client import TranslaasClient, TranslaasOptions

class TestTranslaasClient:
    def setup_method(self):
        """Set up test fixtures."""
        self.options = TranslaasOptions(
            api_key='test-api-key',
            base_url='https://api.test.com',
        )
        self.client = TranslaasClient(self.options)

    @pytest.mark.asyncio
    async def test_get_entry_returns_translation_when_entry_exists(self):
        """Test that get_entry returns translation when entry exists."""
        # Arrange
        mock_response = AsyncMock()
        mock_response.text = 'Save'
        mock_response.raise_for_status = AsyncMock()

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            # Act
            result = await self.client.get_entry('ui', 'button.save', 'en')

            # Assert
            assert result == 'Save'

    @pytest.mark.asyncio
    async def test_get_entry_raises_exception_when_api_returns_error(self):
        """Test that get_entry raises exception when API returns error."""
        # Arrange
        import httpx
        mock_response = AsyncMock()
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            'Not Found',
            request=AsyncMock(),
            response=mock_response
        )
        mock_response.status_code = 404

        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(return_value=mock_response)

            # Act & Assert
            with pytest.raises(Exception) as exc_info:
                await self.client.get_entry('ui', 'button.save', 'en')

            assert 'API request failed' in str(exc_info.value)
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests for specific file
pytest tests/test_client.py

# Run tests with coverage
pytest --cov=translaas --cov-report=html

# Run tests in watch mode
pytest-watch

# Run type checking
mypy translaas/

# Run linting
ruff check .

# Format code
black translaas/ tests/
```

## Additional Resources

- [SDK Guidelines](.cursor/rules/translaas-sdk-rules.mdc) - Comprehensive development guidelines including TDD practices
- [Architecture Documentation](docs/ARCHITECTURE.md) - Architecture overview and design patterns (if available)
- [API Reference](docs/API_REFERENCE.md) - Complete API reference (if available)

## Release Notes and Version Management

### Version Management

The SDK uses Semantic Versioning (SemVer) for version management. Version numbers follow the format `MAJOR.MINOR.PATCH`.

#### Version Numbering

We follow [Semantic Versioning](https://semver.org/) (SemVer):
- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (0.Y.0): New features, backward compatible
- **PATCH** (0.0.Z): Bug fixes, backward compatible

#### Version Location

Version is managed in:
- `pyproject.toml` - `[project]` section, `version` field
- Or `translaas/__init__.py` - `__version__` variable

#### When to Update Version

Update version for:
- ✅ New features (MINOR bump)
- ✅ Bug fixes (PATCH bump)
- ✅ Breaking changes (MAJOR bump)
- ✅ Documentation updates that affect usage (PATCH bump)

**Don't update version for:**
- ❌ Internal refactoring with no user-facing changes
- ❌ Test-only changes
- ❌ Build system changes that don't affect published packages
- ❌ Documentation-only changes (unless they affect API usage)

#### Version Release Process

**Manual Process:**

1. **Update version** in `pyproject.toml` or `__init__.py`:
   ```python
   # pyproject.toml
   [project]
   version = "1.2.0"

   # Or __init__.py
   __version__ = "1.2.0"
   ```

2. **Update CHANGELOG.md** with release notes

3. **Build the package**:
   ```bash
   python -m build
   ```

4. **Test the build**:
   ```bash
   pip install dist/translaas-*.whl
   ```

5. **Tag the release**:
   ```bash
   git tag v1.2.0
   git push origin v1.2.0
   ```

6. **Publish to PyPI** (if you have permissions):
   ```bash
   twine upload dist/*
   ```

#### Pre-Release Versions

For pre-release versions, use version numbers like:
- `0.1.0` - Initial pre-release
- `0.2.0` - Pre-release with new features
- `0.1.1` - Pre-release bug fix

Once stable, release `1.0.0` as the first stable version.

---

### Release Notes

## Version 0.1.0 (Pre-Release)

### Initial Pre-Release

This is the initial pre-release of the Translaas SDK for Python. This version is still under active development and may have breaking changes before the 1.0.0 release.

### Features

- ✅ Strongly-typed API with full type hints support
- ✅ Convenience API via `TranslaasService` with `t()` method
- ✅ Framework integrations for Flask, FastAPI, and Django
- ✅ Flexible caching with configurable cache modes (None, Entry, Group, Project)
- ✅ Offline caching with file-based storage
- ✅ Hybrid caching (memory L1 + file L2) for optimal performance
- ✅ Multi-environment support (Python 3.8+, CPython, PyPy)
- ✅ Fully asynchronous API for optimal performance
- ✅ Modular design - use only what you need

### Supported Environments

- Python 3.8+
- CPython
- PyPy 3.8+

### Installation

```bash
# Full package (recommended)
pip install translaas

# Or install from source
pip install -e ".[dev]"
```

### Documentation

- [README.md](README.md) - Getting started guide
- [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution guidelines
- [GitHub Repository](https://github.com/acuencadev/translaas-sdk-python)

### Breaking Changes

None - This is the initial pre-release.

### Known Issues

None at this time.

---

### Template for Future Releases

When adding a new release, add it at the top of the "Release Notes" section above, following this template:

```markdown
## Version X.Y.Z

### Added
- New features added in this release

### Changed
- Changes to existing functionality

### Fixed
- Bug fixes

### Deprecated
- Features that will be removed in a future release

### Removed
- Features removed in this release

### Security
- Security fixes
```

Thank you for contributing to Translaas SDK! 🎉
