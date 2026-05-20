"""Response models for the Translaas SDK."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from translaas.models.enums import PluralCategory


class TranslationGroup:
    """Represents a group of translation entries.

    A translation group contains multiple translation entries, which can be
    either simple string values or plural forms.

    Attributes:
        entries: Dictionary mapping entry keys to their translation values or plural forms.
        entry_context: Optional per-entry context map from the API when `includeContext` was requested.
        version: Optional translation bundle version from the API response.
        generated_at: Optional ISO timestamp from the API (`generatedAt`).
        project: Optional project identifier echoed by the API.
        lang: Optional language code echoed by the API.
    """

    def __init__(
        self,
        entries: Optional[Dict[str, Any]] = None,
        *,
        entry_context: Optional[Dict[str, Dict[str, str]]] = None,
        version: Optional[int] = None,
        generated_at: Optional[str] = None,
        project: Optional[str] = None,
        lang: Optional[str] = None,
    ) -> None:
        """Initialize a TranslationGroup.

        Args:
            entries: Optional dictionary of translation entries. Defaults to empty dict.
            entry_context: Optional nested context map from the API.
            version: Optional bundle version integer from the API.
            generated_at: Optional `generatedAt` timestamp string.
            project: Optional project field from the API payload.
            lang: Optional language field from the API payload.
        """
        self.entries: Dict[str, Any] = entries if entries is not None else {}
        self.entry_context: Optional[Dict[str, Dict[str, str]]] = entry_context
        self.version: Optional[int] = version
        self.generated_at: Optional[str] = generated_at
        self.project: Optional[str] = project
        self.lang: Optional[str] = lang

    def get_value(self, key: str) -> Optional[str]:
        """Get a simple translation value for the given key.

        Returns the translation value if it's a simple string, or None if
        the entry has plural forms or doesn't exist.

        Args:
            key: The entry key to retrieve.

        Returns:
            The translation value as a string, or None if not found or has plural forms.
        """
        entry = self.entries.get(key)
        if isinstance(entry, str):
            return entry
        return None

    def get_plural_forms(self, key: str) -> Optional[Dict[PluralCategory, str]]:
        """Get all plural forms for the given key.

        Returns a dictionary mapping plural categories to their translation
        values if the entry has plural forms, or None if it doesn't.

        Args:
            key: The entry key to retrieve plural forms for.

        Returns:
            Dictionary mapping PluralCategory to translation strings, or None if not found.
        """
        entry = self.entries.get(key)
        if isinstance(entry, dict):
            # Filter to only include valid plural category keys
            plural_forms: Dict[PluralCategory, str] = {}
            for category in PluralCategory:
                if category.value in entry:
                    plural_forms[category] = entry[category.value]
            return plural_forms if plural_forms else None
        return None

    def has_plural_forms(self, key: str) -> bool:
        """Check if an entry has plural forms.

        Args:
            key: The entry key to check.

        Returns:
            True if the entry has plural forms, False otherwise.
        """
        entry = self.entries.get(key)
        return isinstance(entry, dict)

    def get_plural_form(self, key: str, category: PluralCategory) -> Optional[str]:
        """Get a specific plural form for the given key and category.

        Args:
            key: The entry key to retrieve.
            category: The plural category to retrieve.

        Returns:
            The translation value for the specified plural category, or None if not found.
        """
        forms = self.get_plural_forms(key)
        if forms:
            return forms.get(category)
        return None


class TranslationProject:
    """Represents a complete translation project with multiple groups.

    A translation project contains multiple translation groups, each
    representing a logical grouping of translations.

    Attributes:
        groups: Dictionary mapping group names to their translation entries (nested dicts).
        group_entry_context: Optional `groupEntryContext` from the API when `includeContext` was used.
    """

    def __init__(
        self,
        groups: Optional[Dict[str, Any]] = None,
        *,
        group_entry_context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Initialize a TranslationProject.

        Args:
            groups: Optional dictionary of translation groups. Defaults to empty dict.
            group_entry_context: Optional nested context from the API.
        """
        self.groups: Dict[str, Any] = groups if groups is not None else {}
        self.group_entry_context: Optional[Dict[str, Any]] = group_entry_context

    def get_group(self, group_name: str) -> Optional[TranslationGroup]:
        """Get a translation group by name.

        Args:
            group_name: The name of the group to retrieve.

        Returns:
            A TranslationGroup instance if found, or None if not found.
        """
        group_data = self.groups.get(group_name)
        if group_data is None:
            return None

        if isinstance(group_data, dict):
            if "entries" in group_data and isinstance(group_data["entries"], dict):
                return TranslationGroup(entries=group_data["entries"])
            return TranslationGroup(entries=group_data)
        return None


@dataclass
class OfflineCacheDownloadResult:
    """Result of downloading the offline translation ZIP bundle."""

    not_modified: bool = False
    etag: Optional[str] = None
    suggested_file_name: Optional[str] = None
    content: Optional[bytes] = None


class ProjectLocales:
    """Represents the list of locales available for a translation project.

    Attributes:
        locales: List of locale codes (language codes) available for the project.
        project: Optional project identifier from the API response.
        last_modified_utc: Optional `lastModifiedUtc` from the API (ISO timestamp).
    """

    def __init__(
        self,
        locales: Optional[List[str]] = None,
        *,
        project: Optional[str] = None,
        last_modified_utc: Optional[str] = None,
    ) -> None:
        """Initialize a ProjectLocales instance.

        Args:
            locales: Optional list of locale codes. Defaults to empty list.
            project: Optional project field from the API.
            last_modified_utc: Optional last-modified timestamp from the API.
        """
        self.locales: List[str] = locales if locales is not None else []
        self.project: Optional[str] = project
        self.last_modified_utc: Optional[str] = last_modified_utc
