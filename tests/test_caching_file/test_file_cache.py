"""Tests for the file cache provider."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from translaas.caching_file.file_cache import CacheMetadata, FileCacheProvider, sanitize_project_id
from translaas.caching_file.offline_models import MANIFEST_VERSION
from translaas.models.protocols import ITranslaasCacheProvider
from translaas.models.responses import ProjectLocales, TranslationProject


class TestCacheMetadata:
    """Tests for CacheMetadata class."""

    def test_cache_metadata_creation(self) -> None:
        now = datetime.now(timezone.utc)
        metadata = CacheMetadata(created_at=now)
        assert metadata.created_at == now
        assert metadata.expires_at is None

    def test_cache_metadata_with_expiration(self) -> None:
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        metadata = CacheMetadata(created_at=now, expires_at=expires)
        assert not metadata.is_expired()

    def test_cache_metadata_expired(self) -> None:
        now = datetime.now(timezone.utc)
        expires = now - timedelta(hours=1)
        metadata = CacheMetadata(created_at=now, expires_at=expires)
        assert metadata.is_expired()

    def test_cache_metadata_to_dict(self) -> None:
        now = datetime.now(timezone.utc)
        metadata = CacheMetadata(
            created_at=now,
            project_id="test-project",
            language="en",
        )
        data = metadata.to_dict()
        assert data["created_at"] == now.isoformat()
        assert data["project_id"] == "test-project"


class TestFileCacheProvider:
    """Tests for FileCacheProvider (spec §7.6 layout)."""

    @pytest.fixture
    def temp_cache_dir(self) -> Path:
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_protocol_compliance(self, temp_cache_dir: Path) -> None:
        cache: ITranslaasCacheProvider = FileCacheProvider(str(temp_cache_dir))
        assert isinstance(cache, FileCacheProvider)

    def test_initialization_custom_directory(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        assert cache.cache_directory.resolve() == temp_cache_dir.resolve()
        assert temp_cache_dir.exists()

    def test_save_and_get_project(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})
        cache.save_project("project1", "en", project)
        retrieved = cache.get_project("project1", "en")
        assert retrieved is not None
        assert retrieved.groups == {"group1": {"entry1": "value1"}}

    def test_on_disk_layout(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"common": {"hello": "Hello"}})
        cache.save_project("my-project", "en", project)
        project_path = (
            temp_cache_dir
            / sanitize_project_id("my-project")
            / sanitize_project_id("en")
            / "project.json"
        )
        assert project_path.exists()
        manifest_path = temp_cache_dir / "manifest.json"
        assert manifest_path.exists()
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["version"] == MANIFEST_VERSION

    def test_get_group(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"common": {"hello": "Hello"}})
        cache.save_project("project1", "en", project)
        group = cache.get_group("project1", "common", "en")
        assert group is not None
        assert group.get_value("hello") == "Hello"

    def test_save_and_get_locales(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        locales = ProjectLocales(locales=["en", "de"], project="project1")
        cache.save_project_locales("project1", locales)
        retrieved = cache.get_project_locales("project1")
        assert retrieved is not None
        assert retrieved.locales == ["en", "de"]

    def test_get_project_not_found(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        assert cache.get_project("nonexistent", "en") is None

    def test_remove_project(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})
        cache.save_project("project1", "en", project)
        cache.remove_project("project1", "en")
        assert cache.get_project("project1", "en") is None

    def test_clear(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        cache.save_project("project1", "en", TranslationProject(groups={"g": {"e": "v"}}))
        cache.clear()
        assert cache.get_project("project1", "en") is None

    def test_cleanup_expired(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        cache.set(
            "project|project:project1|lang:en",
            json.dumps({"group1": {"entry1": "value1"}}),
            absolute_expiration_ms=-3600000,
        )
        cache.save_project("project2", "fr", TranslationProject(groups={"g": {"e": "v"}}))
        removed = cache.cleanup_expired()
        assert removed >= 1
        assert cache.get_project("project1", "en") is None
        assert cache.get_project("project2", "fr") is not None

    def test_protocol_get_method(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        cache.save_project(
            "project1",
            "en",
            TranslationProject(groups={"group1": {"entry1": "value1"}}),
        )
        result = cache.get("project|project:project1|lang:en")
        assert result is not None
        assert json.loads(result) == {"group1": {"entry1": "value1"}}

    def test_protocol_set_method(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        cache.set("project|project:project1|lang:en", json.dumps({"group1": {"entry1": "v"}}))
        project = cache.get_project("project1", "en")
        assert project is not None
        assert project.groups["group1"]["entry1"] == "v"

    def test_special_characters_in_project_id(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})
        cache.save_project("project/with/slashes", "en", project)
        retrieved = cache.get_project("project/with/slashes", "en")
        assert retrieved is not None

    def test_corrupted_cache_file(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        path = cache._project_file_path("project1", "en")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("invalid json", encoding="utf-8")
        assert cache.get_project("project1", "en") is None
        assert not path.exists()

    def test_get_manifest_updates_on_save(self, temp_cache_dir: Path) -> None:
        cache = FileCacheProvider(str(temp_cache_dir))
        cache.save_project("project1", "en", TranslationProject(groups={"g": {"e": "v"}}))
        manifest = cache.get_manifest()
        assert sanitize_project_id("project1") in manifest.projects
