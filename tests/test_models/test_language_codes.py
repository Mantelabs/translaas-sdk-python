"""Tests for language code constants."""

from translaas.models.language_codes import LanguageCodes


class TestLanguageCodes:
    """Tests for LanguageCodes constants."""

    def test_major_languages(self) -> None:
        """Test major language codes."""
        assert LanguageCodes.ENGLISH == "en"
        assert LanguageCodes.FRENCH == "fr"
        assert LanguageCodes.SPANISH == "es"
        assert LanguageCodes.GERMAN == "de"
        assert LanguageCodes.ITALIAN == "it"
        assert LanguageCodes.PORTUGUESE == "pt"
        assert LanguageCodes.RUSSIAN == "ru"
        assert LanguageCodes.JAPANESE == "ja"
        assert LanguageCodes.CHINESE == "zh"
        assert LanguageCodes.KOREAN == "ko"

    def test_european_languages(self) -> None:
        """Test European language codes."""
        assert LanguageCodes.DUTCH == "nl"
        assert LanguageCodes.POLISH == "pl"
        assert LanguageCodes.TURKISH == "tr"
        assert LanguageCodes.GREEK == "el"
        assert LanguageCodes.CZECH == "cs"
        assert LanguageCodes.SWEDISH == "sv"
        assert LanguageCodes.NORWEGIAN == "no"
        assert LanguageCodes.DANISH == "da"
        assert LanguageCodes.FINNISH == "fi"
        assert LanguageCodes.HUNGARIAN == "hu"
        assert LanguageCodes.ROMANIAN == "ro"

    def test_asian_languages(self) -> None:
        """Test Asian language codes."""
        assert LanguageCodes.HINDI == "hi"
        assert LanguageCodes.THAI == "th"
        assert LanguageCodes.VIETNAMESE == "vi"
        assert LanguageCodes.INDONESIAN == "id"
        assert LanguageCodes.MALAY == "ms"
        assert LanguageCodes.ARABIC == "ar"
        assert LanguageCodes.HEBREW == "he"

    def test_additional_languages(self) -> None:
        """Test additional language codes."""
        assert LanguageCodes.UKRAINIAN == "uk"
        assert LanguageCodes.BULGARIAN == "bg"
        assert LanguageCodes.CROATIAN == "hr"
        assert LanguageCodes.SERBIAN == "sr"
        assert LanguageCodes.SLOVAK == "sk"
        assert LanguageCodes.SLOVENIAN == "sl"

    def test_language_codes_are_strings(self) -> None:
        """Test that all language codes are strings."""
        assert isinstance(LanguageCodes.ENGLISH, str)
        assert isinstance(LanguageCodes.FRENCH, str)
        assert isinstance(LanguageCodes.SPANISH, str)
        assert isinstance(LanguageCodes.CHINESE, str)

    def test_language_codes_format(self) -> None:
        """Test that language codes follow ISO 639-1 format (2 characters)."""
        assert len(LanguageCodes.ENGLISH) == 2
        assert len(LanguageCodes.FRENCH) == 2
        assert len(LanguageCodes.SPANISH) == 2
        assert len(LanguageCodes.CHINESE) == 2
