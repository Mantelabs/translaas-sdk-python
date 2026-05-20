"""Placeholder substitution for offline translation templates."""

from __future__ import annotations

import re
from typing import Dict, Mapping, Optional, Union


class ParameterReplacer:
    """Replace ``{{name}}``, ``{name}``, and ``%name%`` placeholders."""

    @staticmethod
    def replace(
        text: str,
        parameters: Optional[Mapping[str, Union[str, int, float, None]]] = None,
        *,
        number: Optional[float] = None,
    ) -> str:
        merged = ParameterReplacer._merge_number(number, parameters)
        if not merged:
            return text

        result = text
        for key, value in merged.items():
            escaped = re.escape(key)
            string_value = ParameterReplacer._to_string(value)
            result = re.sub(r"\{\{" + escaped + r"\}\}", string_value, result)
        for key, value in merged.items():
            escaped = re.escape(key)
            string_value = ParameterReplacer._to_string(value)
            result = re.sub(
                r"(?<!\{)\{" + escaped + r"\}(?!\})",
                string_value,
                result,
            )
        for key, value in merged.items():
            escaped = re.escape(key)
            string_value = ParameterReplacer._to_string(value)
            result = re.sub(r"%" + escaped + r"%", string_value, result)
        return result

    @staticmethod
    def _merge_number(
        number: Optional[float],
        parameters: Optional[Mapping[str, Union[str, int, float, None]]],
    ) -> Dict[str, str]:
        merged: Dict[str, str] = {}
        if parameters:
            for key, value in parameters.items():
                merged[key] = ParameterReplacer._to_string(value)
        if number is not None and "N" not in merged and "n" not in merged:
            merged["N"] = format(number, "g")
        return merged

    @staticmethod
    def _to_string(value: Union[str, int, float, None]) -> str:
        if value is None:
            return ""
        if isinstance(value, float):
            return format(value, "g")
        return str(value)
