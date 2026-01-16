# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2026-01-16

### Added
- SSL certificate verification control via `verify` parameter in `TranslaasOptions`
- Support for disabling SSL verification for local development with self-signed certificates
- `TRANSLAAS_VERIFY` environment variable support in Flask and Django extensions
- Basic Python example demonstrating SDK usage without frameworks

### Fixed
- SSL certificate verification errors when connecting to local development APIs with self-signed certificates

### Changed
- All examples now use `.env` files for configuration instead of hardcoded values
- Examples include `.env.example` templates for easy setup
- Updated example README files with `.env` setup instructions

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

## [0.1.0] - 2025-01-14

### Added
- Initial pre-release version
- Project structure and configuration files
- Package configuration with `pyproject.toml`
- Development tool configurations (pytest, mypy, ruff, black)
- Directory structure for translaas package and subpackages
- Test directory structure
- Examples directory structure
- Version management system
- Development environment setup scripts

[Unreleased]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/acuencadev/translaas-sdk-python/releases/tag/v0.1.0
