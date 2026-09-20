"""CLDR cardinal plural category resolution for offline cache reads.

Uses Babel ``Locale.plural_form`` so locales such as Arabic, Polish, and French
select ``zero`` / ``two`` / ``few`` / ``one`` instead of an English-like
``n == 1`` heuristic. Pass a full BCP-47 tag (``pt`` vs ``pt-PT``). Invalid or
empty language tags fall back to the base language, then ``en``.

Live HTTP ``get_entry`` is unchanged — the server still selects from ``n``.
"""

from __future__ import annotations

import functools
from typing import Optional

from babel import Locale, UnknownLocaleError

from translaas.models.enums import PluralCategory

_ENGLISH_LOCALE = "en"

_KEYWORD_MAP = {
    "zero": PluralCategory.ZERO,
    "one": PluralCategory.ONE,
    "two": PluralCategory.TWO,
    "few": PluralCategory.FEW,
    "many": PluralCategory.MANY,
}


class PluralResolver:
    """Resolve CLDR cardinal plural categories from a number and language tag."""

    @staticmethod
    def normalize_language_code(lang: Optional[str]) -> str:
        """Extract the base language from a locale tag.

        Examples: ``en-US`` → ``en``, ``fr-CA`` → ``fr``, ``en_US`` → ``en``.
        Empty or ``None`` input returns ``en``. This helper is not the locale
        passed to Babel on the first attempt; ``resolve_category`` uses the
        full BCP-47 tag so ``pt`` and ``pt-PT`` can differ.

        Args:
            lang: Language or locale code.

        Returns:
            Base language code in lowercase, or ``en`` when ``lang`` is blank.
        """
        if not lang or not isinstance(lang, str):
            return _ENGLISH_LOCALE
        trimmed = lang.strip().replace("_", "-")
        if not trimmed:
            return _ENGLISH_LOCALE
        return trimmed.split("-")[0].lower() or _ENGLISH_LOCALE

    @staticmethod
    def resolve_category(number: Optional[float], lang: Optional[str] = None) -> PluralCategory:
        """Resolve the CLDR cardinal category for ``number`` and ``lang``.

        Args:
            number: Count used for plural selection. When ``None``, returns
                ``PluralCategory.OTHER``.
            lang: BCP-47 language tag (hyphens or underscores). Empty or
                invalid tags fall back to ``en``.

        Returns:
            The CLDR plural category.
        """
        if number is None:
            return PluralCategory.OTHER
        locale = _locale_for_lang(lang)
        keyword = locale.plural_form(number)
        return _map_keyword(keyword)


def _locale_for_lang(lang: Optional[str]) -> Locale:
    tag = _normalize_locale_tag(lang)
    return _create_babel_locale(tag.lower())


def _normalize_locale_tag(lang: Optional[str]) -> str:
    if lang is None or not isinstance(lang, str):
        return _ENGLISH_LOCALE
    trimmed = lang.strip().replace("_", "-")
    return trimmed if trimmed else _ENGLISH_LOCALE


@functools.lru_cache(maxsize=256)
def _create_babel_locale(tag: str) -> Locale:
    locale = _try_parse_locale(tag)
    if locale is not None:
        return locale
    base_language = _base_language(tag)
    if base_language.lower() != tag.lower():
        locale = _try_parse_locale(base_language)
        if locale is not None:
            return locale
    english = _try_parse_locale(_ENGLISH_LOCALE)
    if english is not None:
        return english
    return Locale.parse(_ENGLISH_LOCALE)


def _base_language(locale: str) -> str:
    separator = locale.find("-")
    if separator <= 0:
        return locale
    return locale[:separator]


def _try_parse_locale(tag: str) -> Optional[Locale]:
    if not _looks_like_bcp47(tag):
        return None
    try:
        return Locale.parse(tag, sep="-")
    except (UnknownLocaleError, ValueError):
        return None


def _looks_like_bcp47(locale: str) -> bool:
    """Accept tags such as ``en``, ``pt-PT``, ``zh-Hans-CN``.

    Rejects free text so Babel does not silently use an unexpected default.
    """
    if len(locale) < 2:
        return False

    first_segment = True
    segment_length = 0
    for char in locale:
        if char == "-":
            if segment_length == 0 or (first_segment and segment_length < 2):
                return False
            first_segment = False
            segment_length = 0
            continue
        is_letter = ("A" <= char <= "Z") or ("a" <= char <= "z")
        is_digit = "0" <= char <= "9"
        if first_segment:
            if not is_letter:
                return False
        elif not is_letter and not is_digit:
            return False
        segment_length += 1
        if segment_length > 8:
            return False
    return segment_length >= 2 if first_segment else segment_length >= 1


def _map_keyword(keyword: str) -> PluralCategory:
    return _KEYWORD_MAP.get(keyword, PluralCategory.OTHER)
