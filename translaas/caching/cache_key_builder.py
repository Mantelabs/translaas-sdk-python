"""Cache key builder aligned with Translaas .NET SDK (colon-separated keys)."""

from __future__ import annotations

from typing import Dict, List, Optional


class CacheKeyBuilder:
    """Build consistent cache keys for translation data."""

    _SEP = ":"

    @staticmethod
    def build_entry_key(
        group: str,
        entry: str,
        lang: str,
        number: Optional[float] = None,
        parameters: Optional[Dict[str, str]] = None,
        *,
        project: Optional[str] = None,
        channel: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        if group is None:
            raise TypeError("group is required")
        if entry is None:
            raise TypeError("entry is required")
        if lang is None:
            raise TypeError("lang is required")

        parts: List[str] = ["entry", group, entry, lang]
        if number is not None:
            parts.append(format(number, ".15g"))
        if parameters:
            for key in sorted(parameters.keys(), key=lambda k: k.lower()):
                val = parameters[key]
                if key is not None and val is not None:
                    parts.append(f"{key.lower()}={val}")
        return CacheKeyBuilder._append_snapshot_suffix(
            parts, project=project, channel=channel, version=version, include_context=None
        )

    @staticmethod
    def build_group_key(
        project: str,
        group: str,
        lang: str,
        format: Optional[str] = None,
        *,
        channel: Optional[str] = None,
        version: Optional[str] = None,
        include_context: Optional[bool] = None,
    ) -> str:
        if project is None:
            raise TypeError("project is required")
        if group is None:
            raise TypeError("group is required")
        if lang is None:
            raise TypeError("lang is required")

        parts: List[str] = ["group", project, group, lang]
        if format and format.strip():
            parts.append(format)
        return CacheKeyBuilder._append_snapshot_suffix(
            parts, project=None, channel=channel, version=version, include_context=include_context
        )

    @staticmethod
    def build_project_key(
        project: str,
        lang: str,
        format: Optional[str] = None,
        *,
        channel: Optional[str] = None,
        version: Optional[str] = None,
        include_context: Optional[bool] = None,
    ) -> str:
        if project is None:
            raise TypeError("project is required")
        if lang is None:
            raise TypeError("lang is required")

        parts: List[str] = ["project", project, lang]
        if format and format.strip():
            parts.append(format)
        return CacheKeyBuilder._append_snapshot_suffix(
            parts, project=None, channel=channel, version=version, include_context=include_context
        )

    @staticmethod
    def build_locales_key(
        project: str,
        *,
        channel: Optional[str] = None,
        version: Optional[str] = None,
    ) -> str:
        if project is None:
            raise TypeError("project is required")
        parts: List[str] = ["locales", project]
        return CacheKeyBuilder._append_snapshot_suffix(
            parts, project=None, channel=channel, version=version, include_context=None
        )

    @staticmethod
    def build_offline_cache_key(
        project: str,
        *,
        channel: Optional[str] = None,
        version: Optional[str] = None,
        include_context: Optional[bool] = None,
    ) -> str:
        if project is None:
            raise TypeError("project is required")
        parts: List[str] = ["offline", project]
        return CacheKeyBuilder._append_snapshot_suffix(
            parts, project=None, channel=channel, version=version, include_context=include_context
        )

    @staticmethod
    def _append_snapshot_suffix(
        parts: List[str],
        *,
        project: Optional[str],
        channel: Optional[str],
        version: Optional[str],
        include_context: Optional[bool],
    ) -> str:
        key = CacheKeyBuilder._SEP.join(parts)
        suffix_parts: List[str] = []
        if project and project.strip():
            suffix_parts.append(f"proj={project}")
        if channel and channel.strip():
            suffix_parts.append(f"ch={channel}")
        if version and str(version).strip():
            suffix_parts.append(f"v={version}")
        if include_context is not None:
            suffix_parts.append("ic=1" if include_context else "ic=0")
        if suffix_parts:
            key = key + CacheKeyBuilder._SEP + CacheKeyBuilder._SEP.join(suffix_parts)
        return key
