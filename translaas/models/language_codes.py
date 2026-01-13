"""Language code constants for the Translaas SDK."""

from typing import Final


class LanguageCodes:
    """ISO 639-1 language code constants.

    Provides constants for commonly used language codes following the ISO 639-1 standard.
    These codes are used throughout the SDK for language identification.
    """

    # Major languages
    ENGLISH: Final[str] = "en"
    FRENCH: Final[str] = "fr"
    SPANISH: Final[str] = "es"
    GERMAN: Final[str] = "de"
    ITALIAN: Final[str] = "it"
    PORTUGUESE: Final[str] = "pt"
    RUSSIAN: Final[str] = "ru"
    JAPANESE: Final[str] = "ja"
    CHINESE: Final[str] = "zh"
    KOREAN: Final[str] = "ko"

    # Additional European languages
    DUTCH: Final[str] = "nl"
    POLISH: Final[str] = "pl"
    TURKISH: Final[str] = "tr"
    GREEK: Final[str] = "el"
    CZECH: Final[str] = "cs"
    SWEDISH: Final[str] = "sv"
    NORWEGIAN: Final[str] = "no"
    DANISH: Final[str] = "da"
    FINNISH: Final[str] = "fi"
    HUNGARIAN: Final[str] = "hu"
    ROMANIAN: Final[str] = "ro"

    # Additional Asian languages
    HINDI: Final[str] = "hi"
    THAI: Final[str] = "th"
    VIETNAMESE: Final[str] = "vi"
    INDONESIAN: Final[str] = "id"
    MALAY: Final[str] = "ms"
    ARABIC: Final[str] = "ar"
    HEBREW: Final[str] = "he"

    # Additional languages
    UKRAINIAN: Final[str] = "uk"
    BULGARIAN: Final[str] = "bg"
    CROATIAN: Final[str] = "hr"
    SERBIAN: Final[str] = "sr"
    SLOVAK: Final[str] = "sk"
    SLOVENIAN: Final[str] = "sl"
