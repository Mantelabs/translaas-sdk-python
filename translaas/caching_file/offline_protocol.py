"""Protocol for offline file cache providers."""

from typing import Optional, Protocol

from translaas.caching_file.offline_models import CacheManifest
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject


class IOfflineCacheProvider(Protocol):
    """File-based offline cache (spec §7.6 on-disk layout)."""

    def get_project(self, project: str, lang: str) -> Optional[TranslationProject]:
        """Return cached project data, or None if missing/expired."""
        ...

    def get_group(self, project: str, group: str, lang: str) -> Optional[TranslationGroup]:
        """Return a cached group from the project bundle."""
        ...

    def get_project_locales(self, project: str) -> Optional[ProjectLocales]:
        """Return cached locales for a project."""
        ...

    def save_project(self, project: str, lang: str, data: TranslationProject) -> None:
        """Persist a project bundle for a language."""
        ...

    def save_project_locales(self, project: str, locales: ProjectLocales) -> None:
        """Persist locales for a project."""
        ...

    def is_cached(self, project: str, lang: str) -> bool:
        """Return True when a non-expired project file exists."""
        ...

    def clear_all(self) -> None:
        """Remove the entire cache directory tree."""
        ...

    def clear_project(self, project: str) -> None:
        """Remove cached data for one project."""
        ...

    def get_manifest(self) -> CacheManifest:
        """Read or create the root manifest."""
        ...
