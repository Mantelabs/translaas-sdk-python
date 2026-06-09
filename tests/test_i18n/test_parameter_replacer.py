"""Tests for ParameterReplacer."""

from translaas.i18n.parameter_replacer import ParameterReplacer


def test_double_brace_replacement() -> None:
    result = ParameterReplacer.replace("Hello {{name}}!", {"name": "World"})
    assert result == "Hello World!"


def test_single_brace_replacement() -> None:
    result = ParameterReplacer.replace("Hello {name}!", {"name": "World"})
    assert result == "Hello World!"


def test_percent_legacy_replacement() -> None:
    result = ParameterReplacer.replace("Hello %name%!", {"name": "World"})
    assert result == "Hello World!"


def test_number_injection() -> None:
    result = ParameterReplacer.replace("{N} items", number=5)
    assert result == "5 items"


def test_number_injection_skips_when_lowercase_n_present() -> None:
    result = ParameterReplacer.replace("{n} items", {"n": "9"}, number=5)
    assert result == "9 items"
