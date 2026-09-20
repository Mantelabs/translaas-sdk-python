"""Shared CLDR plural golden / anti-bucket rows aligned with the .NET SDK."""

from __future__ import annotations

from typing import Tuple

from translaas.models.enums import PluralCategory

GoldenRow = Tuple[str, float, PluralCategory]

GOLDEN_PLURAL_ROWS: list[GoldenRow] = [
    ("ar", 0, PluralCategory.ZERO),
    ("ar", 2, PluralCategory.TWO),
    ("pl", 2, PluralCategory.FEW),
    ("fr", 0, PluralCategory.ONE),
    ("en", 0, PluralCategory.OTHER),
    ("en", 1, PluralCategory.ONE),
]

ANTI_BUCKET_PLURAL_ROWS: list[GoldenRow] = [
    ("he", 2, PluralCategory.TWO),
    ("ja", 1, PluralCategory.OTHER),
    ("pt", 0, PluralCategory.ONE),
    ("pt-PT", 0, PluralCategory.OTHER),
    ("bg", 2, PluralCategory.OTHER),
    ("es", 0, PluralCategory.OTHER),
    ("fr-CA", 0, PluralCategory.ONE),
    ("ar_EG", 0, PluralCategory.ZERO),
]

INVERT_LANGUAGE_ROWS: list[GoldenRow] = [
    ("fr", 0, PluralCategory.ONE),
    ("ru", 2, PluralCategory.FEW),
]

GOLDEN_GET_ENTRY_ROWS: list[tuple[str, float, str]] = [
    ("ar", 0, "FORM:zero"),
    ("ar", 2, "FORM:two"),
    ("pl", 2, "FORM:few"),
    ("fr", 0, "FORM:one"),
    ("en", 0, "FORM:other"),
    ("en", 1, "FORM:one"),
    ("pt", 0, "FORM:one"),
    ("pt-PT", 0, "FORM:other"),
]
