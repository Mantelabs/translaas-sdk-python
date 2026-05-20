"""File-based offline cache provider (HTTP spec §7.6 on-disk layout)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Union

from translaas import __version__ as sdk_version
from translaas.caching_file.offline_models import (
    MANIFEST_VERSION,
    CachedLocales,
    CachedProject,
    CacheManifest,
    CacheSyncStatus,
    ProjectCacheInfo,
)
from translaas.exceptions import TranslaasOfflineCacheException
from translaas.models.options import OfflineCacheOptions
from translaas.models.protocols import ITranslaasCacheProvider
from translaas.models.responses import ProjectLocales, TranslationGroup, TranslationProject

_MANIFEST_FILE = "manifest.json"
_LOCALES_FILE = "locales.json"
_PROJECT_FILE = "project.json"


def sanitize_project_id(project_id: str) -> str:
    """Sanitize a project id for use as a filesystem segment."""
    invalid = set('<>:"/\\|?*')
    return "".join("_" if ch in invalid else ch for ch in project_id)


class CacheMetadata:
    """Legacy metadata type retained for existing unit tests."""

    def __init__(
        self,
        created_at: datetime,
        expires_at: Optional[datetime] = None,
        project_id: Optional[str] = None,
        language: Optional[str] = None,
        format: Optional[str] = None,
    ) -> None:
        self.created_at = created_at
        self.expires_at = expires_at
        self.project_id = project_id
        self.language = language
        self.format = format

    def is_expired(self, now: Optional[datetime] = None) -> bool:
        if self.expires_at is None:
            return False
        if now is None:
            now = datetime.now(timezone.utc)
        return now >= self.expires_at

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"created_at": self.created_at.isoformat()}
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
        created_at_str = data.get("created_at", "")
        created_at = datetime.fromisoformat(created_at_str.replace("Z", "+00:00"))
        expires_at = None
        if data.get("expires_at"):
            expires_at = datetime.fromisoformat(str(data["expires_at"]).replace("Z", "+00:00"))
        return cls(
            created_at=created_at,
            expires_at=expires_at,
            project_id=data.get("project_id"),
            language=data.get("language"),
            format=data.get("format"),
        )


class FileCacheProvider(ITranslaasCacheProvider):
    """Offline cache using ``manifest.json`` and per-project locale trees."""

    def __init__(
        self,
        cache_directory: Union[str, OfflineCacheOptions] = ".translaas-cache",
    ) -> None:
        if isinstance(cache_directory, OfflineCacheOptions):
            directory = cache_directory.cache_directory
        elif isinstance(cache_directory, str):
            directory = cache_directory
        else:
            raise TypeError("cache_directory must be a path string or OfflineCacheOptions")
        if not directory or not str(directory).strip():
            raise ValueError("cache_directory is required")
        self.cache_directory = _resolve_cache_directory(str(directory))
        self._ensure_cache_directory()

    # --- Offline cache API ---

    def get_project(self, project: str, lang: str) -> Optional[TranslationProject]:
        _validate_project_lang(project, lang)
        path = self._project_file_path(project, lang)
        cached = _read_wrapper(path, CachedProject.from_dict, remove_on_error=True)
        if cached is None:
            return None
        if _is_expired(cached.expires_at):
            path.unlink(missing_ok=True)
            return None
        return cached.data

    def remove_project(self, project: str, lang: str) -> None:
        """Remove a cached project language bundle."""
        path = self._project_file_path(project, lang)
        if path.exists():
            path.unlink()

    def get_group(self, project: str, group: str, lang: str) -> Optional[TranslationGroup]:
        if not group or not str(group).strip():
            raise ValueError("group is required")
        project_data = self.get_project(project, lang)
        if project_data is None:
            return None
        return project_data.get_group(group)

    def get_project_locales(self, project: str) -> Optional[ProjectLocales]:
        if not project or not str(project).strip():
            raise ValueError("project is required")
        path = self._locales_file_path(project)
        cached = _read_wrapper(path, CachedLocales.from_dict, remove_on_error=True)
        if cached is None:
            return None
        if _is_expired(cached.expires_at):
            return None
        return cached.data

    def save_project(self, project: str, lang: str, data: TranslationProject) -> None:
        _validate_project_lang(project, lang)
        path = self._project_file_path(project, lang)
        wrapper = CachedProject(cached_at=_iso_now(), data=data)
        _write_json_atomic(path, wrapper.to_dict())
        self._update_manifest_for_project(project, lang, CacheSyncStatus.SYNCED)

    def save_project_locales(self, project: str, locales: ProjectLocales) -> None:
        if not project or not str(project).strip():
            raise ValueError("project is required")
        path = self._locales_file_path(project)
        wrapper = CachedLocales(cached_at=_iso_now(), data=locales)
        _write_json_atomic(path, wrapper.to_dict())

    def is_cached(self, project: str, lang: str) -> bool:
        return self.get_project(project, lang) is not None

    def clear_all(self) -> None:
        if self.cache_directory.exists():
            shutil.rmtree(self.cache_directory, ignore_errors=True)
        self._ensure_cache_directory()

    def clear_project(self, project: str) -> None:
        if not project or not str(project).strip():
            raise ValueError("project is required")
        project_dir = self._project_directory(project)
        if project_dir.exists():
            shutil.rmtree(project_dir, ignore_errors=True)
        manifest = self.get_manifest()
        sanitized = sanitize_project_id(project)
        manifest.projects.pop(sanitized, None)
        manifest.projects.pop(project, None)
        _write_json_atomic(self._manifest_path(), manifest.to_dict())

    def get_manifest(self) -> CacheManifest:
        path = self._manifest_path()
        if not path.exists():
            return _new_manifest()
        try:
            with open(path, encoding="utf-8") as handle:
                data = json.load(handle)
            if isinstance(data, dict):
                return CacheManifest.from_dict(data)
        except (OSError, json.JSONDecodeError):
            pass
        return _new_manifest()

    def apply_offline_bundle(
        self,
        project: str,
        locales: Optional[ProjectLocales],
        projects_by_lang: Dict[str, TranslationProject],
    ) -> None:
        """Write parsed ZIP/API bundle payloads to disk."""
        if locales is not None:
            self.save_project_locales(project, locales)
        for lang, project_data in projects_by_lang.items():
            self.save_project(project, lang, project_data)

    # --- ITranslaasCacheProvider (HTTP in-memory cache L2) ---

    def get(self, key: str) -> Optional[str]:
        parsed = _parse_pipe_cache_key(key)
        if parsed is None:
            return None
        project_id, language, _format = parsed
        project = self.get_project(project_id, language)
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
        del sliding_expiration_ms  # not supported for file L2
        parsed = _parse_pipe_cache_key(key)
        if parsed is None:
            return
        project_id, language, _format = parsed
        try:
            project_data = json.loads(value)
            project = TranslationProject(groups=project_data)
            self.save_project(project_id, language, project)
            if absolute_expiration_ms is not None:
                path = self._project_file_path(project_id, language)
                _set_wrapper_expiration(path, absolute_expiration_ms)
        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    def remove(self, key: str) -> None:
        parsed = _parse_pipe_cache_key(key)
        if parsed is None:
            return
        project_id, language, _format = parsed
        path = self._project_file_path(project_id, language)
        if path.exists():
            path.unlink()

    def clear(self) -> None:
        self.clear_all()

    def cleanup_expired(self) -> int:
        removed = 0
        if not self.cache_directory.exists():
            return 0
        for project_dir in self.cache_directory.iterdir():
            if not project_dir.is_dir():
                continue
            locales_path = project_dir / _LOCALES_FILE
            if locales_path.is_file() and _remove_if_expired(locales_path):
                removed += 1
            for lang_dir in project_dir.iterdir():
                if not lang_dir.is_dir():
                    continue
                project_path = lang_dir / _PROJECT_FILE
                if project_path.is_file() and _remove_if_expired(project_path):
                    removed += 1
        return removed

    # --- Path helpers ---

    def _manifest_path(self) -> Path:
        return self.cache_directory / _MANIFEST_FILE

    def _project_directory(self, project: str) -> Path:
        return self.cache_directory / sanitize_project_id(project)

    def _language_directory(self, project: str, lang: str) -> Path:
        return self._project_directory(project) / sanitize_project_id(lang)

    def _project_file_path(self, project: str, lang: str) -> Path:
        return self._language_directory(project, lang) / _PROJECT_FILE

    def _locales_file_path(self, project: str) -> Path:
        return self._project_directory(project) / _LOCALES_FILE

    def _ensure_cache_directory(self) -> None:
        self.cache_directory.mkdir(parents=True, exist_ok=True)

    def _update_manifest_for_project(
        self,
        project: str,
        lang: str,
        status: CacheSyncStatus,
    ) -> None:
        manifest = self.get_manifest()
        key = sanitize_project_id(project)
        info = manifest.projects.get(key) or ProjectCacheInfo()
        if lang not in info.languages:
            info.languages.append(lang)
        info.last_sync_at = _iso_now()
        info.status = status
        manifest.projects[key] = info
        manifest.last_sync_at = _iso_now()
        _write_json_atomic(self._manifest_path(), manifest.to_dict())


def _resolve_cache_directory(cache_directory: str) -> Path:
    path = Path(cache_directory)
    if not path.is_absolute():
        path = Path.cwd() / path
    return path


def _validate_project_lang(project: str, lang: str) -> None:
    if not project or not str(project).strip():
        raise ValueError("project is required")
    if not lang or not str(lang).strip():
        raise ValueError("lang is required")


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_manifest() -> CacheManifest:
    return CacheManifest(
        version=MANIFEST_VERSION,
        sdk_version=sdk_version,
        created_at=_iso_now(),
    )


def _read_wrapper(path: Path, factory, *, remove_on_error: bool = False):  # type: ignore[no-untyped-def]
    if not path.exists():
        return None
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict):
            return factory(data)
    except OSError as ex:
        raise TranslaasOfflineCacheException(
            f"Failed to read cache file '{path.name}'.",
            inner_error=ex,
        ) from ex
    except (json.JSONDecodeError, TypeError, ValueError):
        if remove_on_error:
            path.unlink(missing_ok=True)
        return None
    return None


def _write_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = Path(str(path) + ".tmp")
    try:
        with open(temp_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
        os.replace(temp_path, path)
    except OSError as ex:
        if temp_path.exists():
            temp_path.unlink(missing_ok=True)
        raise TranslaasOfflineCacheException(
            f"Failed to write cache file '{path.name}'.",
            inner_error=ex,
        ) from ex


def _is_expired(expires_at: Optional[str]) -> bool:
    if not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(str(expires_at).replace("Z", "+00:00"))
    except ValueError:
        return False
    return datetime.now(timezone.utc) >= expiry


def _remove_if_expired(path: Path) -> bool:
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if isinstance(data, dict) and _is_expired(data.get("expiresAt")):
            path.unlink(missing_ok=True)
            return True
    except (OSError, json.JSONDecodeError):
        path.unlink(missing_ok=True)
        return True
    return False


def _set_wrapper_expiration(path: Path, absolute_expiration_ms: int) -> None:
    if not path.exists():
        return
    try:
        with open(path, encoding="utf-8") as handle:
            data = json.load(handle)
        if not isinstance(data, dict):
            return
        expires = datetime.now(timezone.utc) + timedelta(milliseconds=absolute_expiration_ms)
        data["expiresAt"] = expires.isoformat()
        _write_json_atomic(path, data)
    except (OSError, json.JSONDecodeError):
        pass


def _parse_pipe_cache_key(key: str) -> Optional[tuple[str, str, Optional[str]]]:
    parts = key.split("|")
    project_id: Optional[str] = None
    language: Optional[str] = None
    format_spec: Optional[str] = None
    for part in parts:
        if part.startswith("project:"):
            project_id = part.split(":", 1)[1]
        elif part.startswith("lang:"):
            language = part.split(":", 1)[1]
        elif part.startswith("format:"):
            format_spec = part.split(":", 1)[1]
    if project_id is None or language is None:
        return None
    return project_id, language, format_spec
