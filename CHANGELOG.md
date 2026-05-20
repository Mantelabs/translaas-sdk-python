# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `TranslaasRequestContext` and `SdkTranslationQueryParams` for per-request channel, version, project, and conditional GET.
- `CacheKeyBuilder` with .NET-compatible colon-separated cache keys.
- `sdk_translations_path_prefix` and `default_sdk_query` on `TranslaasOptions`.
- `OfflineCacheDownloadResult` for offline ZIP downloads (ETag, filename, `not_modified`).
- `format=flat-json` composite-key parsing for project responses.
- Text query auto-injects plural parameter `N` when `n` is set (invariant formatting).

### Changed

- **Breaking:** `get_offline_cache` returns `OfflineCacheDownloadResult` instead of raw `bytes`.
- **Breaking:** In-memory cache keys use `CacheKeyBuilder` format (invalidates prior cache entries).
- 204/304 responses match .NET client semantics (empty fallbacks instead of exceptions when uncached).
- `report_missing_keys` with an empty list performs no HTTP request.
- API error messages prefer JSON `{code, message}` envelopes when present.

## [0.3.0b1] - 2026-04-06

### Added

- SDK HTTP paths aligned with the Translation Delivery API under `/sdk/v1/` (parity with the JavaScript SDK).
- `translaas.client.parsing` helpers for translation groups, projects, and locales responses.
- `TranslaasOptions` fields: `default_project`, `channel`, `snapshot_version`, `include_context`, `use_conditional_requests`, and `api_key_header`.
- `normalize_translaas_base_url()` so `base_url` may omit or include `/sdk/v1` consistently.
- `ReportMissingKeyItem` and `ValidateApiKeyResult` in `translaas.models.sdk_payloads`.
- `TranslaasService` / client support for reporting missing keys and validating API keys.
- Django settings: `TRANSLAAS_DEFAULT_PROJECT`, `TRANSLAAS_CHANNEL`, `TRANSLAAS_SNAPSHOT_VERSION` (extension wiring).

### Changed

- **Breaking:** In-repo framework examples under `examples/` were removed; local example apps belong outside the tracked tree (see `.gitignore` and README).

### Fixed

- Stronger response body typing when reading `httpx` responses in the client.
- Source distributions are pruned to the intended tree (`MANIFEST.in` and explicit `translaas*` package discovery), so local `examples/` or `venv/` folders are not bundled into the sdist.

## [0.1.2] - 2026-01-16

### Added
- SSL certificate verification control via `verify` parameter in `TranslaasOptions`
- Support for disabling SSL verification for local development with self-signed certificates
- `TRANSLAAS_VERIFY` environment variable support in Flask and Django extensions
- Basic Python example demonstrating SDK usage without frameworks
- Response body extraction in API error messages for better debugging

### Fixed
- SSL certificate verification errors when connecting to local development APIs with self-signed certificates
- Parameter spreading in API requests to match JavaScript SDK implementation (parameters now spread directly into query params instead of being serialized as JSON)
- FastAPI extension now properly manages async context manager lifecycle for TranslaasService instances

### Changed
- All examples now use `.env` files for configuration instead of hardcoded values
- Examples include `.env.example` templates for easy setup
- Updated example README files with `.env` setup instructions
- Improved error messages in `TranslaasApiException` to include API response body when available
- `TranslaasClient.get_entry()` now spreads parameters directly into query parameters, matching JavaScript SDK behavior

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

[Unreleased]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.3.0b1...HEAD
[0.3.0b1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.2...v0.3.0b1
[0.1.2]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/acuencadev/translaas-sdk-python/releases/tag/v0.1.0
