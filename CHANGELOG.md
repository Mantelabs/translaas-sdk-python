# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.5.0b1] - 2026-06-09

Minor beta release on **0.4.0b1**. Resolves default project id from the validate API key response for multi-project keys and aligns `t()` / offline plural and parameter behavior with the .NET SDK (**0.4.1-beta** line). Coordinated with JS **0.5.0-beta** alignment work.

### Added

- **`resolve_default_project_id()`** — shared helper for default project resolution from validate responses ([#44](https://github.com/acuencadev/translaas-sdk-python/pull/44))
- **`ValidateApiKeyResult.project_ids`** and **`default_project_id`** — multi-project API key metadata from `GET /api/v1/api-keys/validate`
- **`TranslaasService.t()`** — .NET-aligned overloads supporting **`number` and `parameters` together** (with or without explicit `lang`) ([#47](https://github.com/acuencadev/translaas-sdk-python/pull/47))
- **`translaas.i18n.offline_helpers`** — offline plural (`one`/`other`) and `{name}` substitution helpers matching .NET `CachingTranslaasClient`

### Changed

- **Breaking (offline):** `CachingTranslaasClient` offline plural selection uses **one/other only** (language-agnostic), matching .NET instead of full CLDR `PluralResolver` rules
- **Breaking (offline):** offline parameter substitution supports **`{name}`** placeholders only (no `{{name}}` or `%name%`), matching .NET `SubstituteParameters`
- **`ParameterReplacer`** — case-insensitive `N` detection when merging plural count into parameters

### Fixed

- Tenant-level API keys without a configured default project fail fast with a clear **`TranslaasConfigurationException`**
- Multi-project API keys resolve the backend default project from validate when `default_project` is omitted

### Migration

1. **From `0.4.0b1`:** bump to **`0.5.0b1`**; set `default_project` explicitly for tenant-level API keys, or rely on validate resolution for multi-project keys.
2. **Offline cache consumers:** re-test plural and interpolated strings if you depended on CLDR-specific offline rules or `{{name}}` / `%name%` placeholders.

## [0.4.0b1] - 2026-05-22

Coordinated **beta** release aligning the Python SDK with the **Translaas SDK v1** HTTP surface, the .NET reference implementation, and JS/Java **0.4.0** / **0.4.0-beta** SDK lines. Builds on **0.3.0b1** / **0.3.0b2** SDK v1 parity work ([#41](https://github.com/acuencadev/translaas-sdk-python/issues/41), [#42](https://github.com/acuencadev/translaas-sdk-python/pull/42)).

### Added

#### Translaas SDK v1 HTTP API

- Configurable **`sdk_translations_path_prefix`** on `TranslaasOptions` (default **`/sdk/v1/translations`**) for text, group, project, locales, report-missing, and offline-cache routes.
- **`TranslaasRequestContext`**, **`SdkTranslationQueryParams`**, and **`CacheKeyBuilder`** for per-request ETags, channel/version query overrides, and L1 cache keys aligned with .NET.
- **`OfflineCacheDownloadResult`** with **`not_modified`** handling for **304** offline ZIP downloads.
- **`translaas.client.parsing`** helpers for group bare maps, project **`format=flat-json`** composite keys, and locales envelopes.
- Text query auto-injects plural parameter **`N`** when **`n`** is set.
- **`report_missing_keys`** with an empty list performs no HTTP request.
- API error messages prefer JSON **`{ "code", "message" }`** envelopes when present.

#### Caching and offline

- **`CachingTranslaasClient`** with **`CACHE_FIRST`**, **`API_FIRST`**, and **`CACHE_ONLY`** offline fallback modes.
- On-disk offline layout aligned with HTTP spec §7.6; **`parse_offline_zip`**, **`OfflineCacheSyncService`**, **`PluralResolver`**, **`ParameterReplacer`**.
- **`create_translaas_client`** / **`create_offline_cache_provider`** factory helpers.
- **`TranslaasService`** wires offline mode when enabled.

#### Service layer and framework integrations

- **`merge_request_context`** and **`TranslaasService`** forwarding of **`request_context`** / **`sdk_query`** on **`t()`**, **`get_entry()`**, **`get_group()`**, **`get_project()`**, **`get_project_locales()`**, and **`get_offline_cache()`**.
- **`CachingTranslaasClient`** passes **`request_context`** through to the inner client on API paths.
- **`fastapi_config()`** helper; FastAPI **`init_app()`** resolves options from **`app.state.translaas_config`**, mapped state keys, or environment (aligned with Django/Flask).
- Django settings: **`TRANSLAAS_DEFAULT_PROJECT`**, **`TRANSLAAS_CHANNEL`**, **`TRANSLAAS_SNAPSHOT_VERSION`** (extension wiring).
- **`normalize_translaas_base_url()`** so **`base_url`** may omit or include **`/sdk/v1`** consistently.
- **`ReportMissingKeyItem`** and **`ValidateApiKeyResult`** in **`translaas.models.sdk_payloads`**.

### Changed

#### HTTP semantics (breaking for some callers)

- **`GET /text`**: HTTP **204** returns the requested entry key as the translation text; HTTP **304** returns cached text when L1 is enabled, otherwise the entry key.
- **`GET /group`**, **`GET /project`**, **`GET /locales`**: HTTP **204** and **304** return **empty model instances** instead of raising or returning **`None`** when uncached.
- **Breaking:** **`get_offline_cache`** returns **`OfflineCacheDownloadResult`** instead of raw **`bytes`**.
- **Breaking:** In-memory cache keys use **`CacheKeyBuilder`** colon format (invalidates prior cache entries).
- **Breaking:** **`FileCacheProvider`** on-disk layout changed from flat **`{project}_{lang}.json`** files to the spec tree (invalidates prior offline cache directories).
- **Breaking:** In-repo framework examples under **`examples/`** were removed; local example apps belong outside the tracked tree (see **`.gitignore`** and README).
- README corrected (single package, offline docs); Django/Flask use shared config builders.

### Fixed

- Stronger response body typing when reading **`httpx`** responses in the client.
- Source distributions are pruned to the intended tree (**`MANIFEST.in`** and explicit **`translaas*`** package discovery).

### Migration

1. Point **`base_url`** at your API host; rely on default **`sdk_translations_path_prefix`** or set it explicitly during migration from legacy **`/api/translations/...`** paths.
2. Replace **`None`** / exception expectations on group/project/locale bundle methods with empty-model semantics or **`OfflineCacheDownloadResult.not_modified`** handling.
3. Clear L1 caches or restart processes after upgrade because cache key format changed.
4. Re-sync offline bundles if you used the pre-spec flat-file disk layout.

SDK v1 HTTP parity (Phases A–C for [#41](https://github.com/acuencadev/translaas-sdk-python/issues/41)).

### Added

- `TranslaasRequestContext`, `SdkTranslationQueryParams`, `CacheKeyBuilder`, and `OfflineCacheDownloadResult`.
- `sdk_translations_path_prefix`, `default_sdk_query`, and `format=flat-json` composite-key project parsing.
- Text query auto-injects plural parameter `N` when `n` is set (invariant formatting).
- `CachingTranslaasClient` with `CACHE_FIRST`, `API_FIRST`, and `CACHE_ONLY` offline fallback modes.
- On-disk offline layout aligned with HTTP spec §7.6; `parse_offline_zip`, `OfflineCacheSyncService`, `PluralResolver`, `ParameterReplacer`.
- `create_translaas_client` / `create_offline_cache_provider`; `TranslaasService` wires offline mode when enabled.
- Meta-repo sample `examples/python/offline-node`; extended `build_translaas_options` / `from_env` / framework config helpers.

### Changed

- **Breaking:** `FileCacheProvider` on-disk layout changed from flat `{project}_{lang}.json` files to the spec tree (invalidates prior offline cache directories).
- **Breaking:** `get_offline_cache` returns `OfflineCacheDownloadResult` instead of raw `bytes`.
- **Breaking:** In-memory cache keys use `CacheKeyBuilder` format (invalidates prior cache entries).
- 204/304 responses match .NET client semantics (empty fallbacks instead of exceptions when uncached).
- `report_missing_keys` with an empty list performs no HTTP request.
- API error messages prefer JSON `{code, message}` envelopes when present.
- README corrected (single package, offline docs); Django/Flask use shared config builders; version `0.3.0b2`.

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

[Unreleased]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.4.0b1...HEAD
[0.4.0b1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.3.0b2...v0.4.0b1
[0.3.0b2]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.3.0b1...v0.3.0b2
[0.3.0b1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.2...v0.3.0b1
[0.1.2]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/acuencadev/translaas-sdk-python/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/acuencadev/translaas-sdk-python/releases/tag/v0.1.0
