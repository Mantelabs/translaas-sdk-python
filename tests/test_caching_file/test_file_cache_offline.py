"""Additional offline file cache coverage."""

import json
import tempfile

from translaas.caching_file.file_cache import FileCacheProvider
from translaas.models.responses import ProjectLocales, TranslationProject


def test_clear_project_and_apply_bundle() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCacheProvider(tmpdir)
        cache.save_project("demo", "en", TranslationProject(groups={"g": {"e": "v"}}))
        cache.clear_project("demo")
        assert cache.get_project("demo", "en") is None

        cache.apply_offline_bundle(
            "demo",
            ProjectLocales(locales=["en", "de"]),
            {
                "en": TranslationProject(groups={"common": {"hello": "Hi"}}),
                "de": TranslationProject(groups={"common": {"hello": "Hallo"}}),
            },
        )
        assert cache.get_project_locales("demo") is not None
        assert cache.get_project("demo", "de") is not None
        assert cache.is_cached("demo", "en")


def test_save_project_with_entry_context() -> None:
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = FileCacheProvider(tmpdir)
        project = TranslationProject(
            groups={"common": {"hello": "Hi"}},
            group_entry_context={"common": {"hello": {"screen": "home"}}},
        )
        cache.save_project("demo", "en", project)
        loaded = cache.get_project("demo", "en")
        assert loaded is not None
        assert loaded.group_entry_context is not None
        path = cache._project_file_path("demo", "en")
        raw = json.loads(path.read_text(encoding="utf-8"))
        assert "entryContext" in raw["data"]
