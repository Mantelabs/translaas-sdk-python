# Release v0.5.0b1 — multi-project keys and .NET parity (beta)

## Overview

**`0.5.0b1`** beta on PyPI. Builds on **0.4.0b1** with default project resolution from the validate API key response and .NET-aligned `t()` / offline plural and parameter behavior.

## Package published

- **`translaas==0.5.0b1`** on [PyPI](https://pypi.org/project/translaas/)

## Install

```bash
pip install translaas==0.5.0b1
```

## Highlights

- **Multi-project API keys** — `resolve_default_project_id()` and extended `ValidateApiKeyResult`
- **`t()` overloads** — pass plural `number` and interpolation `parameters` together
- **Offline .NET parity** — one/other plural rules and `{name}` substitution in `CachingTranslaasClient`
- **Breaking (offline)** — plural and placeholder behavior changed to match Translaas.SDK

## Migration

**From `0.4.0b1`:** bump to **`0.5.0b1`**. Re-test offline plural/interpolation if you used CLDR-specific rules or `{{name}}` / `%name%` placeholders.

## Changelog

Full details: **[CHANGELOG.md](https://github.com/acuencadev/translaas-sdk-python/blob/v0.5.0b1/CHANGELOG.md)** — section **`[0.5.0b1]`**.

---

**Full diff**: https://github.com/acuencadev/translaas-sdk-python/compare/v0.4.0b1...v0.5.0b1
