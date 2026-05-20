"""Data models for on-disk offline cache layout (HTTP spec §7.6)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from translaas.models.responses import ProjectLocales, TranslationProject


class CacheSyncStatus(str, Enum):
    """Synchronization status stored in the cache manifest."""

    SYNCED = "synced"
    PENDING = "pending"
    FAILED = "failed"


MANIFEST_VERSION = "1.0"


@dataclass
class ProjectCacheInfo:
    """Per-project entry in ``manifest.json``."""

    languages: List[str] = field(default_factory=list)
    last_sync_at: Optional[str] = None
    status: CacheSyncStatus = CacheSyncStatus.SYNCED


@dataclass
class CacheManifest:
    """Root ``manifest.json`` metadata."""

    version: str = MANIFEST_VERSION
    sdk_version: str = ""
    created_at: str = ""
    last_sync_at: Optional[str] = None
    projects: Dict[str, ProjectCacheInfo] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "version": self.version,
            "sdkVersion": self.sdk_version,
            "createdAt": self.created_at or _iso_now(),
            "lastSyncAt": self.last_sync_at,
            "projects": {
                project_id: {
                    "languages": info.languages,
                    "lastSyncAt": info.last_sync_at,
                    "status": info.status.value,
                }
                for project_id, info in self.projects.items()
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CacheManifest":
        projects_raw = data.get("projects") or {}
        projects: Dict[str, ProjectCacheInfo] = {}
        for project_id, info in projects_raw.items():
            if not isinstance(info, dict):
                continue
            status_raw = info.get("status", CacheSyncStatus.SYNCED.value)
            try:
                status = CacheSyncStatus(status_raw)
            except ValueError:
                status = CacheSyncStatus.SYNCED
            projects[project_id] = ProjectCacheInfo(
                languages=list(info.get("languages") or []),
                last_sync_at=info.get("lastSyncAt"),
                status=status,
            )
        return cls(
            version=str(data.get("version") or MANIFEST_VERSION),
            sdk_version=str(data.get("sdkVersion") or ""),
            created_at=str(data.get("createdAt") or ""),
            last_sync_at=data.get("lastSyncAt"),
            projects=projects,
        )


@dataclass
class CachedProject:
    """Wrapper for ``{project}/{lang}/project.json``."""

    cached_at: str
    data: TranslationProject
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "cachedAt": self.cached_at,
            "expiresAt": self.expires_at,
            "data": _project_to_storage_dict(self.data),
        }
        return payload

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["CachedProject"]:
        if not isinstance(data, dict):
            return None
        inner = data.get("data")
        if not isinstance(inner, dict):
            return None
        return cls(
            cached_at=str(data.get("cachedAt") or _iso_now()),
            expires_at=data.get("expiresAt"),
            data=_project_from_storage_dict(inner),
        )


@dataclass
class CachedLocales:
    """Wrapper for ``{project}/locales.json``."""

    cached_at: str
    data: ProjectLocales
    expires_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cachedAt": self.cached_at,
            "expiresAt": self.expires_at,
            "data": {
                "locales": list(self.data.locales),
                "project": self.data.project,
                "lastModifiedUtc": self.data.last_modified_utc,
            },
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> Optional["CachedLocales"]:
        if not isinstance(data, dict):
            return None
        inner = data.get("data")
        if not isinstance(inner, dict):
            return None
        locales_raw = inner.get("locales")
        locales = list(locales_raw) if isinstance(locales_raw, list) else []
        return cls(
            cached_at=str(data.get("cachedAt") or _iso_now()),
            expires_at=data.get("expiresAt"),
            data=ProjectLocales(
                locales=locales,
                project=inner.get("project"),
                last_modified_utc=inner.get("lastModifiedUtc"),
            ),
        )


def _iso_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _project_to_storage_dict(project: TranslationProject) -> Dict[str, Any]:
    result: Dict[str, Any] = dict(project.groups)
    if project.group_entry_context:
        result["entryContext"] = project.group_entry_context
    return result


def _project_from_storage_dict(data: Dict[str, Any]) -> TranslationProject:
    groups = dict(data)
    entry_context = groups.pop("entryContext", None)
    return TranslationProject(groups=groups, group_entry_context=entry_context)
