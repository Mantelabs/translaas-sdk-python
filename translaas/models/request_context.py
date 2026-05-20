"""Per-request SDK translation options (channel, version, conditional GET)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SdkTranslationQueryParams:
    """Optional query parameters for SDK translation HTTP APIs."""

    channel: Optional[str] = None
    v: Optional[str] = None
    include_context: Optional[bool] = None


@dataclass
class TranslaasRequestContext:
    """Optional per-request options; response fields populated by the client."""

    channel: Optional[str] = None
    version: Optional[str] = None
    project: Optional[str] = None
    include_context: Optional[bool] = None
    if_none_match: Optional[str] = None
    response_etag: Optional[str] = None
    not_modified: bool = False


def prepare_request_context(context: Optional[TranslaasRequestContext]) -> None:
    """Reset response fields before a request."""
    if context is None:
        return
    context.response_etag = None
    context.not_modified = False


def assign_response_context(
    context: Optional[TranslaasRequestContext],
    *,
    etag: Optional[str] = None,
    not_modified: bool = False,
) -> None:
    """Populate response fields after a request."""
    if context is None:
        return
    context.response_etag = etag
    context.not_modified = not_modified


def merge_sdk_query(
    default: Optional[SdkTranslationQueryParams],
    per_call: Optional[SdkTranslationQueryParams],
    *,
    omit_include_context: bool = False,
) -> SdkTranslationQueryParams:
    """Merge default options query with per-call overrides (per-call wins)."""
    out = SdkTranslationQueryParams()
    if default is not None:
        out.channel = default.channel
        out.v = default.v
        if not omit_include_context:
            out.include_context = default.include_context
    if per_call is not None:
        if per_call.channel is not None:
            out.channel = per_call.channel
        if per_call.v is not None:
            out.v = per_call.v
        if not omit_include_context and per_call.include_context is not None:
            out.include_context = per_call.include_context
    return out


def sdk_query_to_params(
    query: SdkTranslationQueryParams,
    *,
    omit_include_context: bool = False,
) -> dict[str, str]:
    """Convert merged SDK query to URL query parameters."""
    params: dict[str, str] = {}
    if query.channel:
        params["channel"] = query.channel
    if query.v:
        params["v"] = query.v
    if not omit_include_context and query.include_context is not None:
        params["includeContext"] = "true" if query.include_context else "false"
    return params


def context_to_sdk_query(
    context: Optional[TranslaasRequestContext],
    *,
    omit_include_context: bool = False,
) -> SdkTranslationQueryParams:
    """Map request context fields to SDK query params."""
    if context is None:
        return SdkTranslationQueryParams()
    ic = None if omit_include_context else context.include_context
    return SdkTranslationQueryParams(
        channel=context.channel,
        v=context.version,
        include_context=ic,
    )
