"""Tests for offline helpers aligned with .NET CachingTranslaasClient."""

from translaas.i18n.offline_helpers import determine_plural_category, substitute_parameters
from translaas.models.enums import PluralCategory


def test_determine_plural_category_one_other() -> None:
    assert determine_plural_category(1) == PluralCategory.ONE
    assert determine_plural_category(0) == PluralCategory.OTHER
    assert determine_plural_category(5) == PluralCategory.OTHER
    assert determine_plural_category(None) == PluralCategory.OTHER


def test_determine_plural_category_ignores_language() -> None:
    assert determine_plural_category(0) == PluralCategory.OTHER
    assert determine_plural_category(1) == PluralCategory.ONE


def test_substitute_parameters_single_placeholder() -> None:
    result = substitute_parameters("Hello {userName}!", {"userName": "John"})
    assert result == "Hello John!"


def test_substitute_parameters_case_insensitive_keys() -> None:
    result = substitute_parameters("Value {n}", {"N": "42"})
    assert result == "Value 42"


def test_substitute_parameters_number_injection() -> None:
    result = substitute_parameters("You have {N} items", number=5)
    assert result == "You have 5 items"


def test_substitute_parameters_explicit_n_wins() -> None:
    result = substitute_parameters("You have {N} items", {"N": "9"}, number=5)
    assert result == "You have 9 items"


def test_substitute_parameters_combined_number_and_params() -> None:
    template = "Hello {userName}, you have {N} items and {pending} pending"
    result = substitute_parameters(
        template,
        {"userName": "John", "pending": "3"},
        number=5,
    )
    assert result == "Hello John, you have 5 items and 3 pending"


def test_substitute_parameters_leaves_unknown_placeholders() -> None:
    result = substitute_parameters("Hello {name}", None)
    assert result == "Hello {name}"
