"""Tests for PluralResolver."""

from translaas.i18n.plural_resolver import PluralResolver
from translaas.models.enums import PluralCategory


def test_english_like() -> None:
    assert PluralResolver.resolve_category(1, "en") == PluralCategory.ONE
    assert PluralResolver.resolve_category(0, "en") == PluralCategory.OTHER
    assert PluralResolver.resolve_category(5, "en-US") == PluralCategory.OTHER


def test_french_like() -> None:
    assert PluralResolver.resolve_category(0, "fr") == PluralCategory.ONE
    assert PluralResolver.resolve_category(2, "fr") == PluralCategory.OTHER


def test_arabic_zero() -> None:
    assert PluralResolver.resolve_category(0, "ar") == PluralCategory.ZERO
    assert PluralResolver.resolve_category(2, "ar") == PluralCategory.TWO


def test_slavic_polish_few() -> None:
    assert PluralResolver.resolve_category(3, "pl") == PluralCategory.FEW


def test_unsupported_language_falls_back_to_english() -> None:
    assert PluralResolver.resolve_category(1, "xx") == PluralCategory.ONE
    assert PluralResolver.resolve_category(2, "xx") == PluralCategory.OTHER
