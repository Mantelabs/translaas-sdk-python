"""Parse offline translation ZIP bundles (HTTP spec §7.6)."""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass, field
from typing import Dict, Optional

from translaas.caching_file.file_cache import sanitize_project_id
from translaas.caching_file.offline_models import (
    CachedLocales,
    CachedProject,
    MANIFEST_VERSION,
)
from translaas.models.responses import ProjectLocales, TranslationProject


@dataclass
class OfflineBundle:
    """Parsed offline ZIP contents."""

    manifest: Dict[str, object]
    locales_by_project: Dict[str, ProjectLocales] = field(default_factory=dict)
    projects_by_project_lang: Dict[str, Dict[str, TranslationProject]] = field(
        default_factory=dict
    )


def parse_offline_zip(content: bytes) -> OfflineBundle:
    """Parse a ZIP offline bundle into structured models."""
    if not content:
        raise ValueError("ZIP content is empty")

    manifest: Dict[str, object] = {}
    locales_by_project: Dict[str, ProjectLocales] = {}
    projects: Dict[str, Dict[str, TranslationProject]] = {}

    with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
        for name in archive.namelist():
            if name.endswith("/"):
                continue
            with archive.open(name) as handle:
                raw = handle.read()

            if name == "manifest.json":
                manifest = _load_json_dict(raw)
                continue

            parts = name.split("/")
            if len(parts) < 2:
                continue
            project_segment = parts[0]
            file_name = parts[-1]

            if file_name == "locales.json" and len(parts) == 2:
                locales = _parse_locales_wrapper(raw)
                if locales is not None:
                    locales_by_project[project_segment] = locales
                continue

            if file_name == "project.json" and len(parts) == 3:
                lang_segment = parts[1]
                project_data = _parse_project_wrapper(raw)
                if project_data is not None:
                    projects.setdefault(project_segment, {})[lang_segment] = project_data

    _validate_manifest(manifest)
    return OfflineBundle(
        manifest=manifest,
        locales_by_project=locales_by_project,
        projects_by_project_lang=projects,
    )


def resolve_project_key(bundle: OfflineBundle, project: str) -> str:
    """Resolve a logical project id to the sanitized folder name used in the ZIP."""
    sanitized = sanitize_project_id(project)
    if sanitized in bundle.projects_by_project_lang or sanitized in bundle.locales_by_project:
        return sanitized
    if project in bundle.projects_by_project_lang or project in bundle.locales_by_project:
        return project
    manifest_projects = bundle.manifest.get("projects")
    if isinstance(manifest_projects, dict):
        if sanitized in manifest_projects:
            return sanitized
        if project in manifest_projects:
            return project
    return sanitized


def _validate_manifest(manifest: Dict[str, object]) -> None:
    version = manifest.get("version")
    if version is not None and str(version) != MANIFEST_VERSION:
        # Forward-compatible: accept unknown versions but keep default constant documented.
        pass


def _load_json_dict(raw: bytes) -> Dict[str, object]:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object in ZIP entry")
    return data


def _parse_locales_wrapper(raw: bytes) -> Optional[ProjectLocales]:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return None
    cached = CachedLocales.from_dict(data)
    return cached.data if cached else None


def _parse_project_wrapper(raw: bytes) -> Optional[TranslationProject]:
    data = json.loads(raw.decode("utf-8"))
    if not isinstance(data, dict):
        return None
    cached = CachedProject.from_dict(data)
    return cached.data if cached else None
