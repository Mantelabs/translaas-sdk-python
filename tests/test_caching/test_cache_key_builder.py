"""Tests for CacheKeyBuilder (.NET parity)."""

from translaas.caching.cache_key_builder import CacheKeyBuilder


class TestCacheKeyBuilder:
    def test_build_entry_key_basic(self) -> None:
        assert CacheKeyBuilder.build_entry_key("ui", "button.save", "en") == "entry:ui:button.save:en"

    def test_build_entry_key_with_number(self) -> None:
        assert (
            CacheKeyBuilder.build_entry_key("messages", "item.count", "en", 5)
            == "entry:messages:item.count:en:5"
        )

    def test_build_entry_key_with_snapshot_suffix(self) -> None:
        key = CacheKeyBuilder.build_entry_key(
            "g",
            "e",
            "en",
            project="p1",
            channel="beta",
            version="01ARZ3NDEKTSV4RRFFQ69G5FAV",
        )
        assert "proj=p1" in key
        assert "ch=beta" in key
        assert key.endswith("v=01ARZ3NDEKTSV4RRFFQ69G5FAV")

    def test_build_group_key_include_context(self) -> None:
        key = CacheKeyBuilder.build_group_key(
            "my-project", "ui", "en", "flat-json", channel="stable", include_context=True
        )
        assert key.startswith("group:my-project:ui:en:flat-json:")
        assert "ch=stable" in key
        assert key.endswith("ic=1")

    def test_build_locales_key(self) -> None:
        assert CacheKeyBuilder.build_locales_key("proj") == "locales:proj"

    def test_build_offline_cache_key(self) -> None:
        key = CacheKeyBuilder.build_offline_cache_key("proj", include_context=False)
        assert key == "offline:proj:ic=0"
