# Release v0.5.1 — first stable 0.5 patch

## Overview

**`0.5.1`** stable on PyPI. Maintenance release on the **0.5** line with no API or runtime behavior changes since **`0.5.0b1`**. Graduates the SDK to **Production/Stable** on PyPI.

## Package published

- **`translaas==0.5.1`** on [PyPI](https://pypi.org/project/translaas/)

## Install

```bash
pip install translaas==0.5.1
```

Or upgrade from beta:

```bash
pip install -U translaas
```

## Highlights

- **Stable release** — first non-beta **0.5.x** on PyPI
- **Toolchain / CI** — ruff 0.15.20, GitHub Actions v7 bumps, consolidated CI workflows
- **Test reliability** — deterministic memory cache expiration tests (macOS CI flake fix)

## Migration

**From `0.5.0b1`:** drop-in replacement. No code changes required.

## Changelog

Full details: **[CHANGELOG.md](https://github.com/Mantelabs/translaas-sdk-python/blob/v0.5.1/CHANGELOG.md)** — section **`[0.5.1]`**.

---

**Full diff**: https://github.com/Mantelabs/translaas-sdk-python/compare/v0.5.0b1...v0.5.1
