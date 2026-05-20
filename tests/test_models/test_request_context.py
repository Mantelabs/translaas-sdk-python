"""Tests for request context helpers."""

from translaas.models.request_context import (
    SdkTranslationQueryParams,
    TranslaasRequestContext,
    merge_request_context,
)


def test_merge_request_context_returns_none_without_input() -> None:
    assert merge_request_context() is None


def test_merge_request_context_merges_sdk_query_and_overrides() -> None:
    ctx = merge_request_context(
        TranslaasRequestContext(channel="stable", version="v1"),
        SdkTranslationQueryParams(channel="beta", v="v2", include_context=True),
        project="my-project",
        if_none_match='"etag"',
    )
    assert ctx is not None
    assert ctx.channel == "beta"
    assert ctx.version == "v2"
    assert ctx.include_context is True
    assert ctx.project == "my-project"
    assert ctx.if_none_match == '"etag"'


def test_merge_request_context_explicit_kwargs_win_over_sdk_query() -> None:
    ctx = merge_request_context(
        sdk_query=SdkTranslationQueryParams(channel="beta", v="v2"),
        channel="release",
        snapshot_version="snap-1",
        include_context=False,
    )
    assert ctx is not None
    assert ctx.channel == "release"
    assert ctx.version == "snap-1"
    assert ctx.include_context is False
