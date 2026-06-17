"""Plural category resolution for offline reads (simplified CLDR rules)."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from translaas.models.enums import PluralCategory


class _PluralPattern(str, Enum):
    ENGLISH_LIKE = "english-like"
    FRENCH_LIKE = "french-like"
    SLAVIC = "slavic"
    ARABIC = "arabic"


_LANGUAGE_PATTERNS: dict[str, _PluralPattern] = {
    "en": _PluralPattern.ENGLISH_LIKE,
    "de": _PluralPattern.ENGLISH_LIKE,
    "nl": _PluralPattern.ENGLISH_LIKE,
    "sv": _PluralPattern.ENGLISH_LIKE,
    "no": _PluralPattern.ENGLISH_LIKE,
    "da": _PluralPattern.ENGLISH_LIKE,
    "fi": _PluralPattern.ENGLISH_LIKE,
    "is": _PluralPattern.ENGLISH_LIKE,
    "fr": _PluralPattern.FRENCH_LIKE,
    "pt": _PluralPattern.FRENCH_LIKE,
    "es": _PluralPattern.FRENCH_LIKE,
    "it": _PluralPattern.FRENCH_LIKE,
    "ca": _PluralPattern.FRENCH_LIKE,
    "gl": _PluralPattern.FRENCH_LIKE,
    "ru": _PluralPattern.SLAVIC,
    "uk": _PluralPattern.SLAVIC,
    "pl": _PluralPattern.SLAVIC,
    "cs": _PluralPattern.SLAVIC,
    "sk": _PluralPattern.SLAVIC,
    "sr": _PluralPattern.SLAVIC,
    "hr": _PluralPattern.SLAVIC,
    "sl": _PluralPattern.SLAVIC,
    "bg": _PluralPattern.SLAVIC,
    "mk": _PluralPattern.SLAVIC,
    "ar": _PluralPattern.ARABIC,
}


class PluralResolver:
    """Resolve plural categories from a number and language code."""

    @staticmethod
    def normalize_language_code(lang: str) -> str:
        if not lang or not isinstance(lang, str):
            return "en"
        return lang.split("-")[0].lower()

    @staticmethod
    def get_pattern(lang: str) -> Optional[_PluralPattern]:
        return _LANGUAGE_PATTERNS.get(PluralResolver.normalize_language_code(lang))

    @staticmethod
    def resolve_category(number: float, lang: str) -> PluralCategory:
        pattern = PluralResolver.get_pattern(lang)
        if pattern is None:
            return PluralResolver._english_like(number)
        if pattern == _PluralPattern.ENGLISH_LIKE:
            return PluralResolver._english_like(number)
        if pattern == _PluralPattern.FRENCH_LIKE:
            return PluralResolver._french_like(number)
        if pattern == _PluralPattern.SLAVIC:
            return PluralResolver._slavic(number, lang)
        if pattern == _PluralPattern.ARABIC:
            return PluralResolver._arabic(number)
        return PluralResolver._english_like(number)

    @staticmethod
    def _english_like(number: float) -> PluralCategory:
        n = abs(number)
        return PluralCategory.ONE if n == 1 else PluralCategory.OTHER

    @staticmethod
    def _french_like(number: float) -> PluralCategory:
        n = abs(number)
        return PluralCategory.ONE if n in (0, 1) else PluralCategory.OTHER

    @staticmethod
    def _slavic(number: float, lang: str) -> PluralCategory:
        normalized = PluralResolver.normalize_language_code(lang)
        n = int(abs(number))
        mod10 = n % 10
        mod100 = n % 100
        if normalized == "pl":
            if n == 1:
                return PluralCategory.ONE
            if 2 <= mod10 <= 4 and (mod100 < 10 or mod100 >= 20):
                return PluralCategory.FEW
            return PluralCategory.MANY
        if normalized in ("cs", "sk"):
            if n == 1:
                return PluralCategory.ONE
            if 2 <= n <= 4:
                return PluralCategory.FEW
            return PluralCategory.MANY
        if mod10 == 1 and mod100 != 11:
            return PluralCategory.ONE
        if 2 <= mod10 <= 4 and (mod100 < 10 or mod100 >= 20):
            return PluralCategory.FEW
        return PluralCategory.MANY

    @staticmethod
    def _arabic(number: float) -> PluralCategory:
        n = int(abs(number))
        if n == 0:
            return PluralCategory.ZERO
        if n == 1:
            return PluralCategory.ONE
        if n == 2:
            return PluralCategory.TWO
        mod100 = n % 100
        if 3 <= mod100 <= 10:
            return PluralCategory.FEW
        if 11 <= mod100 <= 99:
            return PluralCategory.MANY
        return PluralCategory.OTHER
