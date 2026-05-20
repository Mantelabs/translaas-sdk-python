# Python SDK v1 parity checklist (§6)

Formal sign-off for **0.3.0b2** parity with the Translaas SDK HTTP API, .NET reference, and JavaScript SDK **0.3.0-beta** ([issue #41](https://github.com/acuencadev/translaas-sdk-python/issues/41)).

Reference: [translaas-sdk-python-parity-change-plan.md](../../../.docs/translaas-sdk-python-parity-change-plan.md), [translaas-sdk-http-api-spec.md](../../../.docs/translaas-sdk-http-api-spec.md).

| Area | Status | Evidence |
|------|--------|----------|
| HTTP & auth | ✅ | `TranslaasClient` default prefix `/sdk/v1/translations`; `X-Api-Key`; `validate_api_key` → `/api/v1/api-keys/validate` |
| Query `channel`, `v`, `includeContext` | ✅ | `SdkTranslationQueryParams`, `TranslaasRequestContext`, `from_env` / framework config |
| `If-None-Match` / weak ETag | ✅ | `use_conditional_requests`, `TranslaasRequestContext.if_none_match` / `response_etag` |
| `/text` plural `n` + auto `N` | ✅ | `build_text_query_params`, `tests/test_client/test_text_query.py` |
| `/text` 204 / 304 | ✅ | `tests/test_client/test_status_semantics.py` |
| `/group`, `/project`, `/locales` 204 / 304 | ✅ | `tests/test_client/test_status_semantics.py` |
| `format=flat-json` | ✅ | `tests/test_client/test_parsing_flat_json.py` |
| Nested string / plural map | ✅ | `TranslationGroup`, `tests/test_models/test_responses.py` |
| `report-missing` 202; empty → no HTTP | ✅ | `report_missing_keys`, client guard |
| Offline ZIP download | ✅ | `OfflineCacheDownloadResult`, `get_offline_cache` |
| ZIP parse | ✅ | `parse_offline_zip`, `tests/test_offline/test_zip_bundle.py` |
| `CacheKeyBuilder` | ✅ | `tests/test_caching/test_cache_key_builder.py` |
| `CacheMode` behavior | ✅ | `TranslaasClient` cache paths, `tests/test_client/test_client.py` |
| Offline decorator modes | ✅ | `CachingTranslaasClient`, `tests/test_caching_file/test_caching_client.py` |
| On-disk tree §7.6 | ✅ | `FileCacheProvider`, `tests/test_caching_file/test_file_cache.py` |
| `default_project` for text | ✅ | `TranslaasOptions.default_project`, client `get_entry` |
| `TranslaasService` forwards APIs | ✅ | `get_group` / `get_project` / `get_offline_cache`; `t()` + `request_context` / `sdk_query` |
| README accurate | ✅ | Phase C README update |
| Framework config | ✅ | `build_translaas_options`, Django / Flask / FastAPI |

## Checklist (plan §6)

### HTTP & auth

- [x] All routes under configurable `{prefix}` defaulting to `/sdk/v1/translations`
- [x] `X-Api-Key` on SDK routes; validate endpoint on `/api/v1/api-keys/validate`
- [x] `channel`, `v`, `includeContext` query rules match spec §5–6
- [x] `If-None-Match` / weak ETag stored on context

### Reads

- [x] `/text` plural `n` + auto `N` query param (invariant culture)
- [x] `/text` 204 → entry key; 304 → empty string + `not_modified`
- [x] `/group`, `/project`, `/locales` 204 → empty models; 304 → empty + `not_modified`
- [x] `format=flat-json` for project and group
- [x] Nested `string | plural map` deserialization

### Writes / downloads

- [x] `report-missing` → 202; empty keys → no HTTP call
- [x] Offline ZIP download exposes filename + 304 `not_modified`
- [x] Optional ZIP parse → manifest + per-locale project JSON

### Caching

- [x] `CacheKeyBuilder` matches .NET key strings for same inputs
- [x] `CacheMode` entry/group/project/locales behavior unchanged logically
- [x] Offline decorator: cache-first / api-first / cache-only
- [x] On-disk tree matches spec §7.6

### Service

- [x] `default_project` for text when key not project-scoped
- [x] `TranslaasService` forwards new APIs and context

### Docs

- [x] README accurate (no false retry/modular package claims)
- [x] Migration note: breaking cache keys, offline layout, `get_offline_cache` result type (CHANGELOG `[0.3.0b2]`)

## Sign-off

| Role | Name | Date | Version |
|------|------|------|---------|
| Implementation | SDK parity branch `feature/sdk-v1-parity-phase-a` | 2026-05-20 | **0.3.0b2** |
| Tests | `pytest` full suite, coverage ≥ 80% | 2026-05-20 | 439+ passed |

**Approved for beta tag / publish** when CI is green on the parity branch.
