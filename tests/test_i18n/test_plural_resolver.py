"""Tests for Babel-backed PluralResolver CLDR cardinal selection."""

from __future__ import annotations

from typing import Optional

import pytest

from tests.test_i18n.plural_table_data import (
    ANTI_BUCKET_PLURAL_ROWS,
    GOLDEN_PLURAL_ROWS,
    INVERT_LANGUAGE_ROWS,
)
from translaas.i18n.plural_resolver import PluralResolver
from translaas.models.enums import PluralCategory


@pytest.mark.parametrize("lang,number,expected", GOLDEN_PLURAL_ROWS)
def test_resolve_category_golden_rows(lang: str, number: float, expected: PluralCategory) -> None:
    assert PluralResolver.resolve_category(number, lang) == expected


@pytest.mark.parametrize("lang,number,expected", ANTI_BUCKET_PLURAL_ROWS)
def test_resolve_category_anti_bucket_rows(
    lang: str, number: float, expected: PluralCategory
) -> None:
    assert PluralResolver.resolve_category(number, lang) == expected


@pytest.mark.parametrize("lang,number,expected", INVERT_LANGUAGE_ROWS)
def test_resolve_category_inverts_language_ignored_contract(
    lang: str, number: float, expected: PluralCategory
) -> None:
    assert PluralResolver.resolve_category(number, lang) == expected


def test_resolve_category_null_number_returns_other() -> None:
    assert PluralResolver.resolve_category(None, "ar") == PluralCategory.OTHER
    assert PluralResolver.resolve_category(None, "en") == PluralCategory.OTHER


@pytest.mark.parametrize("lang", [None, "", "   "])
def test_resolve_category_blank_lang_falls_back_to_english(lang: Optional[str]) -> None:
    assert PluralResolver.resolve_category(1, lang) == PluralCategory.ONE
    assert PluralResolver.resolve_category(0, lang) == PluralCategory.OTHER


def test_resolve_category_invalid_lang_falls_back_to_english() -> None:
    assert PluralResolver.resolve_category(0, "not a locale!!") == PluralCategory.OTHER
    assert PluralResolver.resolve_category(1, "not a locale!!") == PluralCategory.ONE


def test_resolve_category_underscore_locale() -> None:
    assert PluralResolver.resolve_category(1, "en_US") == PluralCategory.ONE
    assert PluralResolver.resolve_category(0, "ar_EG") == PluralCategory.ZERO


def test_resolve_category_unknown_well_formed_tag_falls_back_to_english() -> None:
    assert PluralResolver.resolve_category(1, "xx") == PluralCategory.ONE
    assert PluralResolver.resolve_category(2, "xx") == PluralCategory.OTHER


def test_resolve_category_decimal_n() -> None:
    assert PluralResolver.resolve_category(1.5, "en") == PluralCategory.OTHER
    assert PluralResolver.resolve_category(1.5, "fr") == PluralCategory.ONE


def test_normalize_language_code() -> None:
    assert PluralResolver.normalize_language_code("en-US") == "en"
    assert PluralResolver.normalize_language_code("fr_CA") == "fr"
    assert PluralResolver.normalize_language_code("") == "en"
    assert PluralResolver.normalize_language_code(None) == "en"
