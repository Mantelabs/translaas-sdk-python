"""Offline plural and parameter helpers aligned with .NET ``CachingTranslaasClient``."""

from __future__ import annotations

import re
from typing import Dict, Mapping, Optional, Union

from translaas.models.enums import PluralCategory


def determine_plural_category(number: Optional[float]) -> PluralCategory:
    """Match .NET offline ``DeterminePluralCategory`` (one/other only; lang ignored)."""
    if number is None:
        return PluralCategory.OTHER
    return PluralCategory.ONE if number == 1 else PluralCategory.OTHER


def _get_param_value(parameters: Mapping[str, str], name: str) -> Optional[str]:
    if name in parameters:
        return parameters[name]
    lowered = name.lower()
    for key, value in parameters.items():
        if key.lower() == lowered:
            return value
    return None


def _has_param_key(parameters: Mapping[str, str], name: str) -> bool:
    return _get_param_value(parameters, name) is not None


def substitute_parameters(
    template: str,
    parameters: Optional[Mapping[str, Union[str, int, float, None]]] = None,
    *,
    number: Optional[float] = None,
) -> str:
    """Mirror .NET offline ``SubstituteParameters`` (``{name}`` placeholders only)."""
    merged: Dict[str, str] = {}
    if parameters:
        for key, value in parameters.items():
            merged[key] = _to_string(value)

    if number is not None and not _has_param_key(merged, "N"):
        merged["N"] = format(number, "g")

    if not merged:
        return template

    def _replace(match: re.Match[str]) -> str:
        name = match.group(1)
        value = _get_param_value(merged, name)
        return value if value is not None else match.group(0)

    return re.sub(r"\{([a-zA-Z0-9_]+)\}", _replace, template)


def _to_string(value: Union[str, int, float, None]) -> str:
    if value is None:
        return ""
    if isinstance(value, float):
        return format(value, "g")
    return str(value)
