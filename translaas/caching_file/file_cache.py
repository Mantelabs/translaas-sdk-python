"""File-based cache provider for the Translaas SDK.

This module provides persistent file-based caching for translation projects,
enabling offline support and cache synchronization.
"""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from translaas.models.protocols import ITranslaasCacheProvider
from translaas.models.responses import TranslationProject


class CacheMetadata:
    """Metadata for a cached file entry.

    Attributes:
        created_at: Timestamp when the cache entry was created.
        expires_at: Optional timestamp when the cache entry expires.
        project_id: The project ID.
        language: The language code.
        format: Optional format specification.
    """

    def __init__(
        self,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        project_id: Optional[str] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> None:
        """Initialize cache metadata.

        Args:
            created_at: Timestamp when the cache entry was created.
            expires_at: Optional timestamp when the cache entry expires.
            project_id: The project ID.
            language: The language code.
            format: Optional format specification.
        """
        self.created_at = created_at
        self.expires_at = expires_at
        self.project_id = project_id
        self.language = language
        self.format = format

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        """Check if the cache entry is expired.

        Args:
            now: Optional current timestamp. Defaults to UTC now.

        Returns:
            True if the entry is expired, False otherwise.
        """
        if self.expires_at is None:
            return False
        if now is None:
            now = datetime.now(timezone.utc)
        return now >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary.

        Returns:
            Dictionary representation of the metadata.
        """
        result: Dict[str, Any] = {
            "created_at": self.created_at.isoformat(),
        }
        if self.expires_at is not None:
            result["expires_at"] = self.expires_at.isoformat()
        if self.project_id is not None:
            result["project_id"] = self.project_id
        if self.language is not None:
            result["language"] = self.language
        if self.format is not None:
            result["format"] = self.format
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheMetadata":
        """Create metadata from dictionary.

        Args:
            data: Dictionary containing metadata.

        Returns:
            CacheMetadata instance.
        """
        created_at_str = data.get("created_at", "")
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))

        expires_at = None
        if "expires_at" in data and data["expires_at"]:
            expires_at_str = data["expires_at"]
            expires_at = datetime.fromisoformat(expires_at_str.replace("Z", "+00:00"))

        return cls(
            created_at=created_at,
            expires_at=expires_at,
            project_id=data.get("project_id"),
            language=data.get("language"),
            format=data.get("format"),
        )


class FileCacheProvider(ITranslaasCacheProvider):
    """File-based cache provider for translation projects.

    Provides persistent file-based caching with support for:
    - Atomic file operations (write to temp, then rename)
    - Cache metadata with expiration tracking
    - Project-level caching
    - Error handling for file operations

    Attributes:
        cache_directory: Directory path for storing cache files.
    """

    def __init__(self, cache_directory: str = ".translaas-cache") -> None:
        """Initialize the file cache provider.

        Args:
            cache_directory: Directory path for storing cache files.
                Defaults to ".translaas-cache".
        """
        self.cache_directory = Path(cache_directory)
        self._ensure_cache_directory()

    def _ensure_cache_directory(self) -> None:
        """Ensure the cache directory exists."""
        try:
            self.cache_directory.mkdir(parents=True, exist_ok=True)
        except OSError:
            # Directory creation failed, will handle in operations
            pass

    def _get_cache_file_path(
        self, project_id: str, language: str, format: Optional[str] = None
    ) -> Path:
        """Get the cache file path for a project.

        Args:
            project_id: The project ID.
            language: The language code.
            format: Optional format specification.

        Returns:
            Path to the cache file.
        """
        # Create a safe filename from project_id, language, and format
        safe_project = project_id.replace("/", "_").replace("\\", "_")
        safe_language = language.replace("/", "_").replace("\\", "_")
        if format:
            safe_format = format.replace("/", "_").replace("\\", "_")
            filename = f"{safe_project}_{safe_language}_{safe_format}.json"
        else:
            filename = f"{safe_project}_{safe_language}.json"
        return self.cache_directory / filename

    def _get_metadata_file_path(self, cache_file_path: Path) -> Path:
        """Get the metadata file path for a cache file.

        Args:
            cache_file_path: Path to the cache file.

        Returns:
            Path to the metadata file.
        """
        return cache_file_path.with_suffix(".meta.json")

    def get_project(
        self, project_id: str, language: str, format: Optional[str] = None
    ) -> Optional[TranslationProject]:
        """Get a cached translation project.

        Args:
            project_id: The project ID.
            language: The language code.
            format: Optional format specification.

        Returns:
            TranslationProject if found and not expired, None otherwise.
        """
        cache_file_path = self._get_cache_file_path(project_id, language, format)
        metadata_file_path = self._get_metadata_file_path(cache_file_path)

        # Check if files exist
        if not cache_file_path.exists() or not metadata_file_path.exists():
            return None

        try:
            # Read and check metadata
            with open(metadata_file_path, encoding="utf-8") as f:
                metadata_dict = json.load(f)
            metadata = CacheMetadata.from_dict(metadata_dict)

            # Check expiration
            if metadata.is_expired():
                # Remove expired files
                self._remove_cache_files(cache_file_path, metadata_file_path)
                return None

            # Read cache file
            with open(cache_file_path, encoding="utf-8") as f:
                project_data = json.load(f)

            return TranslationProject(groups=project_data)
        except (OSError, json.JSONDecodeError, KeyError, ValueError):
            # File errors, JSON errors, or invalid metadata
            # Remove corrupted files
            self._remove_cache_files(cache_file_path, metadata_file_path)
            return None

    def save_project(
        self,
        project: TranslationProject,
        project_id: str,
        language: str,
        format: Optional[str] = None,
        expires_at: Optional[datetime] = None,
    ) -> None:
        """Save a translation project to cache.

        Args:
            project: The TranslationProject to cache.
            project_id: The project ID.
            language: The language code.
            format: Optional format specification.
            expires_at: Optional expiration timestamp.
        """
        cache_file_path = self._get_cache_file_path(project_id, language, format)
        metadata_file_path = self._get_metadata_file_path(cache_file_path)

        # Ensure cache directory exists
        self._ensure_cache_directory()

        # Create metadata
        metadata = CacheMetadata(
            created_at=datetime.now(timezone.utc),
            expires_at=expires_at,
            project_id=project_id,
            language=language,
            format=format,
        )

        try:
            # Atomic write: write to temp file, then rename
            # Write cache file
            with tempfile.NamedTemporaryFile(
                mode="w", dir=self.cache_directory, delete=False, encoding="utf-8", suffix=".json"
            ) as temp_file:
                json.dump(project.groups, temp_file, ensure_ascii=False)
                temp_cache_path = Path(temp_file.name)

            # Write metadata file
            with tempfile.NamedTemporaryFile(
                mode="w",
                dir=self.cache_directory,
                delete=False,
                encoding="utf-8",
                suffix=".meta.json",
            ) as temp_file:
                json.dump(metadata.to_dict(), temp_file, ensure_ascii=False)
                temp_metadata_path = Path(temp_file.name)

            # Atomic rename
            temp_cache_path.replace(cache_file_path)
            temp_metadata_path.replace(metadata_file_path)
        except OSError:
            # File operation failed, clean up temp files
            try:
                if "temp_cache_path" in locals() and temp_cache_path.exists():
                    temp_cache_path.unlink()
                if "temp_metadata_path" in locals() and temp_metadata_path.exists():
                    temp_metadata_path.unlink()
            except OSError:
                pass
            raise

    def _remove_cache_files(self, cache_file_path: Path, metadata_file_path: Path) -> None:
        """Remove cache files safely.

        Args:
            cache_file_path: Path to the cache file.
            metadata_file_path: Path to the metadata file.
        """
        try:
            if cache_file_path.exists():
                cache_file_path.unlink()
            if metadata_file_path.exists():
                metadata_file_path.unlink()
        except OSError:
            # Ignore errors when removing files
            pass

    def remove_project(self, project_id: str, language: str, format: Optional[str] = None) -> None:
        """Remove a cached project.

        Args:
            project_id: The project ID.
            language: The language code.
            format: Optional format specification.
        """
        cache_file_path = self._get_cache_file_path(project_id, language, format)
        metadata_file_path = self._get_metadata_file_path(cache_file_path)
        self._remove_cache_files(cache_file_path, metadata_file_path)

    def clear(self) -> None:
        """Clear all cached projects."""
        try:
            if self.cache_directory.exists():
                for file_path in self.cache_directory.iterdir():
                    if file_path.is_file() and (
                        file_path.suffix == ".json" or file_path.suffixes == [".meta", ".json"]
                    ):
                        try:
                            file_path.unlink()
                        except OSError:
                            pass
        except OSError:
            pass

    def cleanup_expired(self) -> int:
        """Remove all expired cache entries.

        Returns:
            Number of expired entries removed.
        """
        removed_count = 0
        try:
            if not self.cache_directory.exists():
                return 0

            for file_path in self.cache_directory.iterdir():
                if file_path.is_file() and file_path.suffixes == [".meta", ".json"]:
                    try:
                        with open(file_path, encoding="utf-8") as f:
                            metadata_dict = json.load(f)
                        metadata = CacheMetadata.from_dict(metadata_dict)

                        if metadata.is_expired():
                            # Find corresponding cache file
                            cache_file_path = file_path.with_suffix("").with_suffix(".json")
                            self._remove_cache_files(cache_file_path, file_path)
                            removed_count += 1
                    except (OSError, json.JSONDecodeError, KeyError, ValueError):
                        # Corrupted metadata file, remove it
                        try:
                            file_path.unlink()
                            removed_count += 1
                        except OSError:
                            pass
        except OSError:
            pass

        return removed_count

    # ITranslaasCacheProvider protocol implementation
    def get(self, key: str) -> Optional[str]:
        """Get a value from the cache (protocol method).

        This method is provided for protocol compliance but is not recommended
        for file cache. Use get_project() instead for better type safety.

        Args:
            key: The cache key (format: "project|project:{id}|lang:{lang}").

        Returns:
            The cached value as JSON string if found, or None if not found or expired.
        """
        # Parse key format: "project|project:{id}|lang:{lang}|format:{format}"
        parts = key.split("|")
        project_id = None
        language = None
        format_spec = None

        for part in parts:
            if part.startswith("project:"):
                project_id = part.split(":", 1)[1]
            elif part.startswith("lang:"):
                language = part.split(":", 1)[1]
            elif part.startswith("format:"):
                format_spec = part.split(":", 1)[1]

        if project_id is None or language is None:
            return None

        project = self.get_project(project_id, language, format_spec)
        if project is None:
            return None

        return json.dumps(project.groups, ensure_ascii=False)

    def set(
        self,
        key: str,
        value: str,
        absolute_expiration_ms: Optional[int] = None,
        sliding_expiration_ms: Optional[int] = None,
    ) -> None:
        """Set a value in the cache (protocol method).

        This method is provided for protocol compliance but is not recommended
        for file cache. Use save_project() instead for better type safety.

        Args:
            key: The cache key (format: "project|project:{id}|lang:{lang}").
            value: The value to cache (JSON string).
            absolute_expiration_ms: Optional absolute expiration time in milliseconds.
            sliding_expiration_ms: Optional sliding expiration time in milliseconds (not supported).
        """
        # Parse key format
        parts = key.split("|")
        project_id = None
        language = None
        format_spec = None

        for part in parts:
            if part.startswith("project:"):
                project_id = part.split(":", 1)[1]
            elif part.startswith("lang:"):
                language = part.split(":", 1)[1]
            elif part.startswith("format:"):
                format_spec = part.split(":", 1)[1]

        if project_id is None or language is None:
            return

        try:
            project_data = json.loads(value)
            project = TranslationProject(groups=project_data)

            expires_at = None
            if absolute_expiration_ms is not None:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    milliseconds=absolute_expiration_ms
                )

            self.save_project(project, project_id, language, format_spec, expires_at)
        except (json.JSONDecodeError, ValueError):
            # Invalid JSON, skip caching
            pass

    def remove(self, key: str) -> None:
        """Remove a value from the cache (protocol method).

        Args:
            key: The cache key to remove.
        """
        # Parse key format
        parts = key.split("|")
        project_id = None
        language = None
        format_spec = None

        for part in parts:
            if part.startswith("project:"):
                project_id = part.split(":", 1)[1]
            elif part.startswith("lang:"):
                language = part.split(":", 1)[1]
            elif part.startswith("format:"):
                format_spec = part.split(":", 1)[1]

        if project_id is not None and language is not None:
            self.remove_project(project_id, language, format_spec)
