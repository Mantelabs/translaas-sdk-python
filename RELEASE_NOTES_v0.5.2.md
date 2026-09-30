# Release v0.5.2 — offline CLDR plurals

## Overview

**`0.5.2`** stable on PyPI. Patch on the **0.5** line. Offline `get_entry` plural selection now follows CLDR cardinal rules for the request locale, matching the live API.

## Package published

- **`translaas==0.5.2`** on [PyPI](https://pypi.org/project/translaas/)

## Install

```bash
pip install translaas==0.5.2
```

Or upgrade:

```bash
pip install -U translaas
```

## Highlights

- **Offline plurals** — CLDR cardinal categories via Babel, instead of the language-agnostic `1 → one` heuristic
- **`determine_plural_category`** — optional `lang` (BCP-47); omit it to fall back to English CLDR
- **Python 3.8 tests** — `GoldenRow` uses `typing.Tuple` so collection works on 3.8

## Migration

**From `0.5.1`:** drop-in for HTTP-only callers. Re-test offline plural strings if you depended on the old one/other heuristic. Babel (`>=2.18.0,<3`) is now a required dependency.

## Changelog

Full details: **[CHANGELOG.md](https://github.com/Mantelabs/translaas-sdk-python/blob/v0.5.2/CHANGELOG.md)** — section **`[0.5.2]`**.

---

**Full diff**: https://github.com/Mantelabs/translaas-sdk-python/compare/v0.5.1...v0.5.2
