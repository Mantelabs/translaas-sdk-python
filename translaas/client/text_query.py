"""Build query parameters for GET /sdk/v1/translations/text."""

from __future__ import annotations

from typing import Any, Dict, Optional


def merge_number_into_parameters(
    number: Optional[float],
    parameters: Optional[Dict[str, str]],
) -> Optional[Dict[str, str]]:
    """Inject ``N`` (invariant formatting) when ``number`` is set and ``N`` not present."""
    if number is None and not parameters:
        return None

    merged: Dict[str, str] = {}
    if parameters:
        for k, v in parameters.items():
            if k is not None and v is not None:
                merged[k] = v

    if number is not None and "N" not in {k.upper() for k in merged}:
        merged["N"] = format(number, ".15g")

    return merged if merged else None


def build_text_query_params(
    *,
    group: str,
    entry: str,
    lang: str,
    project: Optional[str] = None,
    number: Optional[float] = None,
    parameters: Optional[Dict[str, str]] = None,
    extra_query: Optional[Dict[str, str]] = None,
) -> Dict[str, str]:
    """Build query dict for the text endpoint."""
    merged_params = merge_number_into_parameters(number, parameters)
    req: Dict[str, str] = {
        "group": group,
        "entry": entry,
        "lang": lang,
    }
    if project:
        req["project"] = project
    if number is not None:
        req["n"] = format(number, ".15g")
    if merged_params:
        for k, v in merged_params.items():
            if k == "N":
                req["N"] = v
            elif k.lower() not in {x.lower() for x in req}:
                req[k] = v
    if extra_query:
        for k, v in extra_query.items():
            if v is not None and str(v) != "":
                req[k] = str(v)
    return req
