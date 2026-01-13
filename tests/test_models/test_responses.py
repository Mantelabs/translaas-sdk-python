"""Tests for response models."""


from translaas.models.enums import PluralCategory
from translaas.models.responses import (
    ProjectLocales,
    TranslationGroup,
    TranslationProject,
)


class TestTranslationGroup:
    """Tests for TranslationGroup."""

    def test_create_empty_group(self) -> None:
        """Test creating an empty TranslationGroup."""
        group = TranslationGroup()
        assert group.entries == {}

    def test_create_with_entries(self) -> None:
        """Test creating TranslationGroup with entries."""
        entries = {"key1": "value1", "key2": "value2"}
        group = TranslationGroup(entries=entries)
        assert group.entries == entries

    def test_get_value_simple(self) -> None:
        """Test getting a simple translation value."""
        group = TranslationGroup(entries={"welcome": "Welcome"})
        assert group.get_value("welcome") == "Welcome"

    def test_get_value_not_found(self) -> None:
        """Test getting a value that doesn't exist."""
        group = TranslationGroup()
        assert group.get_value("nonexistent") is None

    def test_get_value_plural_forms_returns_none(self) -> None:
        """Test that get_value returns None for entries with plural forms."""
        group = TranslationGroup(entries={"items": {"one": "1 item", "other": "{count} items"}})
        assert group.get_value("items") is None

    def test_get_plural_forms(self) -> None:
        """Test getting plural forms."""
        entries = {
            "items": {
                "zero": "no items",
                "one": "1 item",
                "other": "{count} items",
            }
        }
        group = TranslationGroup(entries=entries)
        forms = group.get_plural_forms("items")

        assert forms is not None
        assert forms[PluralCategory.ZERO] == "no items"
        assert forms[PluralCategory.ONE] == "1 item"
        assert forms[PluralCategory.OTHER] == "{count} items"

    def test_get_plural_forms_not_found(self) -> None:
        """Test getting plural forms for non-existent entry."""
        group = TranslationGroup()
        assert group.get_plural_forms("nonexistent") is None

    def test_get_plural_forms_simple_value(self) -> None:
        """Test getting plural forms for simple string value."""
        group = TranslationGroup(entries={"welcome": "Welcome"})
        assert group.get_plural_forms("welcome") is None

    def test_has_plural_forms_true(self) -> None:
        """Test checking plural forms for entry with plural forms."""
        group = TranslationGroup(entries={"items": {"one": "1 item", "other": "{count} items"}})
        assert group.has_plural_forms("items") is True

    def test_has_plural_forms_false(self) -> None:
        """Test checking plural forms for simple string value."""
        group = TranslationGroup(entries={"welcome": "Welcome"})
        assert group.has_plural_forms("welcome") is False

    def test_has_plural_forms_not_found(self) -> None:
        """Test checking plural forms for non-existent entry."""
        group = TranslationGroup()
        assert group.has_plural_forms("nonexistent") is False

    def test_get_plural_form(self) -> None:
        """Test getting a specific plural form."""
        entries = {
            "items": {
                "one": "1 item",
                "other": "{count} items",
            }
        }
        group = TranslationGroup(entries=entries)
        assert group.get_plural_form("items", PluralCategory.ONE) == "1 item"
        assert group.get_plural_form("items", PluralCategory.OTHER) == "{count} items"

    def test_get_plural_form_not_found(self) -> None:
        """Test getting plural form for non-existent entry."""
        group = TranslationGroup()
        assert group.get_plural_form("nonexistent", PluralCategory.ONE) is None

    def test_get_plural_form_category_not_present(self) -> None:
        """Test getting plural form for category not present in entry."""
        entries = {"items": {"one": "1 item"}}
        group = TranslationGroup(entries=entries)
        assert group.get_plural_form("items", PluralCategory.ZERO) is None


class TestTranslationProject:
    """Tests for TranslationProject."""

    def test_create_empty_project(self) -> None:
        """Test creating an empty TranslationProject."""
        project = TranslationProject()
        assert project.groups == {}

    def test_create_with_groups(self) -> None:
        """Test creating TranslationProject with groups."""
        groups = {
            "common": {"welcome": "Welcome", "goodbye": "Goodbye"},
            "errors": {"not_found": "Not found"},
        }
        project = TranslationProject(groups=groups)
        assert project.groups == groups

    def test_get_group(self) -> None:
        """Test getting a translation group."""
        groups = {
            "common": {"welcome": "Welcome", "goodbye": "Goodbye"},
        }
        project = TranslationProject(groups=groups)
        group = project.get_group("common")

        assert group is not None
        assert isinstance(group, TranslationGroup)
        assert group.entries == {"welcome": "Welcome", "goodbye": "Goodbye"}

    def test_get_group_not_found(self) -> None:
        """Test getting a group that doesn't exist."""
        project = TranslationProject()
        assert project.get_group("nonexistent") is None

    def test_get_group_with_plural_forms(self) -> None:
        """Test getting a group that contains plural forms."""
        groups = {
            "common": {
                "items": {"one": "1 item", "other": "{count} items"},
            }
        }
        project = TranslationProject(groups=groups)
        group = project.get_group("common")

        assert group is not None
        assert group.has_plural_forms("items") is True


class TestProjectLocales:
    """Tests for ProjectLocales."""

    def test_create_empty_locales(self) -> None:
        """Test creating ProjectLocales with no locales."""
        locales = ProjectLocales()
        assert locales.locales == []

    def test_create_with_locales(self) -> None:
        """Test creating ProjectLocales with locales."""
        locale_list = ["en", "fr", "es", "de"]
        locales = ProjectLocales(locales=locale_list)
        assert locales.locales == locale_list

    def test_locales_property(self) -> None:
        """Test that locales property is accessible."""
        locale_list = ["en", "fr"]
        locales = ProjectLocales(locales=locale_list)
        assert isinstance(locales.locales, list)
        assert len(locales.locales) == 2
