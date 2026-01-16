# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and structure
- Package configuration with `pyproject.toml`
- Development tool configurations (pytest, mypy, ruff, black)
- Directory structure for translaas package and subpackages
- Test directory structure
- Examples directory structure
- Version management system

## [0.1.1] - 2025-01-16

### Added
- Comprehensive testing infrastructure setup
- Shared test fixtures in `tests/conftest.py` (MockCacheProvider, options, client fixtures)
- Test utilities in `tests/helpers.py` for creating mock objects and assertions
- Test fixtures directory with sample JSON data files
- Coverage reporting configuration with 80% minimum threshold
- Integration and unit test markers for better test organization

### Changed
- Refactored existing tests to use shared fixtures from `conftest.py`
- Enhanced pytest configuration with coverage reporting (term, HTML, XML formats)

## [0.1.0] - 2025-01-XX

### Added
- Initial pre-release version
- Project structure and configuration files
- Development environment setup scripts

[Unreleased]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.1...HEAD
[0.1.1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/acuencadev/translaas-sdk-python/releases/tag/v0.1.0
