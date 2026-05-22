# Release v0.4.0b1 — SDK v1 API parity (beta)

## Overview

First **`0.4.0b1`** beta for the Python SDK on PyPI. Aligns with the **Translaas SDK v1** HTTP surface (`/sdk/v1/translations`, API key validation, report-missing, offline ZIP bundles) and ships the full caching and offline stack. Builds on **0.3.0b1** / **0.3.0b2** beta work and matches the JS/Java **0.4.0** / **0.4.0-beta** SDK lines.

## Package published

- **`translaas==0.4.0b1`** on [PyPI](https://pypi.org/project/translaas/)

## Install

```bash
pip install translaas==0.4.0b1
```

## Highlights

- **SDK v1 routes** — configurable `sdk_translations_path_prefix` (default `/sdk/v1/translations`)
- **Caching** — `CacheKeyBuilder` colon keys aligned with .NET; L1 memory cache modes
- **Offline** — `CachingTranslaasClient`, spec §7.6 on-disk layout, plural/parameter resolution
- **Frameworks** — Django, Flask, and FastAPI integrations with shared config builders
- **Service layer** — `request_context` / `sdk_query` forwarding on all read paths
- **Breaking** — empty models on 204/304 bundle reads; new L1 cache key format; new offline disk layout; `get_offline_cache` returns `OfflineCacheDownloadResult`

## What's new in 0.4.0b1 vs 0.3.0b2

- Coordinated **`0.4.0b1`** version line aligned with sibling SDKs.
- `merge_request_context` and `TranslaasService` forwarding of `request_context` / `sdk_query`.
- `fastapi_config()` helper; FastAPI `init_app()` resolves options from app state or environment.

## Migration

**From `0.3.0b1` / `0.3.0b2`:** bump to **`0.4.0b1`**; no additional API changes beyond the items above.

**From legacy `/api/translations/...`:** set **`base_url`** to the API host; use default **`/sdk/v1/translations`** or **`sdk_translations_path_prefix`**.

**Breaking changes (also in 0.3.0b2):**

1. Replace **`None`** checks on bundle methods with empty-model semantics.
2. Invalidate L1 caches after upgrade (key format changed).
3. Re-sync offline bundles if you used the legacy flat-file disk layout.

## Changelog

Full details: **[CHANGELOG.md](https://github.com/acuencadev/translaas-sdk-python/blob/v0.4.0b1/CHANGELOG.md)** — section **`[0.4.0b1]`**.

---

**Full diff**: https://github.com/acuencadev/translaas-sdk-python/compare/v0.3.0b2...v0.4.0b1
