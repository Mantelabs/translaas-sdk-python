"""Tests for the file cache provider."""

import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from translaas.caching_file.file_cache import CacheMetadata, FileCacheProvider
from translaas.models.protocols import ITranslaasCacheProvider
from translaas.models.responses import TranslationProject


class TestCacheMetadata:
    """Tests for CacheMetadata class."""

    def test_cache_metadata_creation(self) -> None:
        """Test cache metadata creation."""
        now = datetime.now(timezone.utc)
        metadata = CacheMetadata(created_at=now)
        assert metadata.created_at == now
        assert metadata.expires_at is None
        assert metadata.project_id is None
        assert metadata.language is None
        assert metadata.format is None

    def test_cache_metadata_with_expiration(self) -> None:
        """Test cache metadata with expiration."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        metadata = CacheMetadata(created_at=now, expires_at=expires)
        assert metadata.expires_at == expires
        assert not metadata.is_expired()

    def test_cache_metadata_expired(self) -> None:
        """Test expired cache metadata."""
        now = datetime.now(timezone.utc)
        expires = now - timedelta(hours=1)
        metadata = CacheMetadata(created_at=now, expires_at=expires)
        assert metadata.is_expired()

    def test_cache_metadata_not_expired(self) -> None:
        """Test non-expired cache metadata."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        metadata = CacheMetadata(created_at=now, expires_at=expires)
        assert not metadata.is_expired()

    def test_cache_metadata_to_dict(self) -> None:
        """Test converting metadata to dictionary."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        metadata = CacheMetadata(
            created_at=now,
            expires_at=expires,
            project_id="test-project",
            language="en",
            format="json",
        )
        data = metadata.to_dict()
        assert data["created_at"] == now.isoformat()
        assert data["expires_at"] == expires.isoformat()
        assert data["project_id"] == "test-project"
        assert data["language"] == "en"
        assert data["format"] == "json"

    def test_cache_metadata_from_dict(self) -> None:
        """Test creating metadata from dictionary."""
        now = datetime.now(timezone.utc)
        expires = now + timedelta(hours=1)
        data = {
            "created_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "project_id": "test-project",
            "language": "en",
            "format": "json",
        }
        metadata = CacheMetadata.from_dict(data)
        assert metadata.created_at == now
        assert metadata.expires_at == expires
        assert metadata.project_id == "test-project"
        assert metadata.language == "en"
        assert metadata.format == "json"

    def test_cache_metadata_from_dict_minimal(self) -> None:
        """Test creating metadata from minimal dictionary."""
        now = datetime.now(timezone.utc)
        data = {"created_at": now.isoformat()}
        metadata = CacheMetadata.from_dict(data)
        assert metadata.created_at == now
        assert metadata.expires_at is None
        assert metadata.project_id is None


class TestFileCacheProvider:
    """Tests for FileCacheProvider class."""

    @pytest.fixture
    def temp_cache_dir(self) -> Path:
        """Create a temporary cache directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_protocol_compliance(self, temp_cache_dir: Path) -> None:
        """Test that FileCacheProvider implements ITranslaasCacheProvider."""
        cache: ITranslaasCacheProvider = FileCacheProvider(str(temp_cache_dir))
        assert isinstance(cache, FileCacheProvider)

    def test_initialization_default(self) -> None:
        """Test default initialization."""
        cache = FileCacheProvider()
        assert cache.cache_directory == Path(".translaas-cache")

    def test_initialization_custom_directory(self, temp_cache_dir: Path) -> None:
        """Test initialization with custom directory."""
        cache = FileCacheProvider(str(temp_cache_dir))
        assert cache.cache_directory == temp_cache_dir
        assert temp_cache_dir.exists()

    def test_save_and_get_project(self, temp_cache_dir: Path) -> None:
        """Test saving and getting a project."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en")
        retrieved = cache.get_project("project1", "en")

        assert retrieved is not None
        assert retrieved.groups == {"group1": {"entry1": "value1"}}

    def test_get_project_not_found(self, temp_cache_dir: Path) -> None:
        """Test getting a project that doesn't exist."""
        cache = FileCacheProvider(str(temp_cache_dir))
        result = cache.get_project("nonexistent", "en")
        assert result is None

    def test_save_project_with_format(self, temp_cache_dir: Path) -> None:
        """Test saving project with format."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en", format="json")
        retrieved = cache.get_project("project1", "en", format="json")

        assert retrieved is not None
        assert retrieved.groups == {"group1": {"entry1": "value1"}}

    def test_save_project_with_expiration(self, temp_cache_dir: Path) -> None:
        """Test saving project with expiration."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})
        expires_at = datetime.now(timezone.utc) + timedelta(hours=1)

        cache.save_project(project, "project1", "en", expires_at=expires_at)
        retrieved = cache.get_project("project1", "en")

        assert retrieved is not None

    def test_get_project_expired(self, temp_cache_dir: Path) -> None:
        """Test getting an expired project."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})
        expires_at = datetime.now(timezone.utc) - timedelta(hours=1)

        cache.save_project(project, "project1", "en", expires_at=expires_at)
        retrieved = cache.get_project("project1", "en")

        assert retrieved is None

    def test_remove_project(self, temp_cache_dir: Path) -> None:
        """Test removing a project."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en")
        assert cache.get_project("project1", "en") is not None

        cache.remove_project("project1", "en")
        assert cache.get_project("project1", "en") is None

    def test_remove_project_not_found(self, temp_cache_dir: Path) -> None:
        """Test removing a project that doesn't exist."""
        cache = FileCacheProvider(str(temp_cache_dir))
        # Should not raise an error
        cache.remove_project("nonexistent", "en")

    def test_clear(self, temp_cache_dir: Path) -> None:
        """Test clearing all cached projects."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project1 = TranslationProject(groups={"group1": {"entry1": "value1"}})
        project2 = TranslationProject(groups={"group2": {"entry2": "value2"}})

        cache.save_project(project1, "project1", "en")
        cache.save_project(project2, "project2", "fr")
        assert cache.get_project("project1", "en") is not None
        assert cache.get_project("project2", "fr") is not None

        cache.clear()
        assert cache.get_project("project1", "en") is None
        assert cache.get_project("project2", "fr") is None

    def test_cleanup_expired(self, temp_cache_dir: Path) -> None:
        """Test cleanup of expired entries."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project1 = TranslationProject(groups={"group1": {"entry1": "value1"}})
        project2 = TranslationProject(groups={"group2": {"entry2": "value2"}})

        # Save with expiration
        expires_past = datetime.now(timezone.utc) - timedelta(hours=1)
        expires_future = datetime.now(timezone.utc) + timedelta(hours=1)

        cache.save_project(project1, "project1", "en", expires_at=expires_past)
        cache.save_project(project2, "project2", "fr", expires_at=expires_future)

        removed = cache.cleanup_expired()
        assert removed == 1
        assert cache.get_project("project1", "en") is None
        assert cache.get_project("project2", "fr") is not None

    def test_cleanup_expired_none(self, temp_cache_dir: Path) -> None:
        """Test cleanup when no entries are expired."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en")
        removed = cache.cleanup_expired()
        assert removed == 0
        assert cache.get_project("project1", "en") is not None

    def test_protocol_get_method(self, temp_cache_dir: Path) -> None:
        """Test protocol get() method."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en")
        result = cache.get("project|project:project1|lang:en")

        assert result is not None
        data = json.loads(result)
        assert data == {"group1": {"entry1": "value1"}}

    def test_protocol_get_method_not_found(self, temp_cache_dir: Path) -> None:
        """Test protocol get() method with nonexistent key."""
        cache = FileCacheProvider(str(temp_cache_dir))
        result = cache.get("project|project:nonexistent|lang:en")
        assert result is None

    def test_protocol_get_method_invalid_key(self, temp_cache_dir: Path) -> None:
        """Test protocol get() method with invalid key format."""
        cache = FileCacheProvider(str(temp_cache_dir))
        result = cache.get("invalid_key")
        assert result is None

    def test_protocol_set_method(self, temp_cache_dir: Path) -> None:
        """Test protocol set() method."""
        cache = FileCacheProvider(str(temp_cache_dir))
        value = json.dumps({"group1": {"entry1": "value1"}})

        cache.set("project|project:project1|lang:en", value)
        project = cache.get_project("project1", "en")

        assert project is not None
        assert project.groups == {"group1": {"entry1": "value1"}}

    def test_protocol_set_method_with_expiration(self, temp_cache_dir: Path) -> None:
        """Test protocol set() method with expiration."""
        cache = FileCacheProvider(str(temp_cache_dir))
        value = json.dumps({"group1": {"entry1": "value1"}})

        cache.set(
            "project|project:project1|lang:en",
            value,
            absolute_expiration_ms=3600000,  # 1 hour
        )
        project = cache.get_project("project1", "en")

        assert project is not None

    def test_protocol_set_method_invalid_json(self, temp_cache_dir: Path) -> None:
        """Test protocol set() method with invalid JSON."""
        cache = FileCacheProvider(str(temp_cache_dir))
        # Should not raise an error
        cache.set("project|project:project1|lang:en", "invalid json")

    def test_protocol_remove_method(self, temp_cache_dir: Path) -> None:
        """Test protocol remove() method."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en")
        assert cache.get_project("project1", "en") is not None

        cache.remove("project|project:project1|lang:en")
        assert cache.get_project("project1", "en") is None

    def test_atomic_write_operation(self, temp_cache_dir: Path) -> None:
        """Test that file writes are atomic."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project1", "en")

        # Verify both cache and metadata files exist
        cache_file = cache._get_cache_file_path("project1", "en")
        metadata_file = cache._get_metadata_file_path(cache_file)

        assert cache_file.exists()
        assert metadata_file.exists()

    def test_special_characters_in_project_id(self, temp_cache_dir: Path) -> None:
        """Test handling special characters in project ID."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project = TranslationProject(groups={"group1": {"entry1": "value1"}})

        cache.save_project(project, "project/with/slashes", "en")
        retrieved = cache.get_project("project/with/slashes", "en")

        assert retrieved is not None
        assert retrieved.groups == {"group1": {"entry1": "value1"}}

    def test_corrupted_cache_file(self, temp_cache_dir: Path) -> None:
        """Test handling corrupted cache file."""
        cache = FileCacheProvider(str(temp_cache_dir))
        cache_file = cache._get_cache_file_path("project1", "en")
        metadata_file = cache._get_metadata_file_path(cache_file)

        # Create corrupted cache file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        # Create valid metadata
        metadata = CacheMetadata(created_at=datetime.now(timezone.utc))
        with open(metadata_file, "w", encoding="utf-8") as f:
            json.dump(metadata.to_dict(), f)

        # Should return None and clean up files
        result = cache.get_project("project1", "en")
        assert result is None
        assert not cache_file.exists()
        assert not metadata_file.exists()

    def test_corrupted_metadata_file(self, temp_cache_dir: Path) -> None:
        """Test handling corrupted metadata file."""
        cache = FileCacheProvider(str(temp_cache_dir))
        cache_file = cache._get_cache_file_path("project1", "en")
        metadata_file = cache._get_metadata_file_path(cache_file)

        # Create valid cache file
        cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cache_file, "w", encoding="utf-8") as f:
            json.dump({"group1": {"entry1": "value1"}}, f)

        # Create corrupted metadata file
        with open(metadata_file, "w", encoding="utf-8") as f:
            f.write("invalid json")

        # Should return None and clean up files
        result = cache.get_project("project1", "en")
        assert result is None
        assert not cache_file.exists()
        assert not metadata_file.exists()

    def test_multiple_projects_same_language(self, temp_cache_dir: Path) -> None:
        """Test caching multiple projects with same language."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project1 = TranslationProject(groups={"group1": {"entry1": "value1"}})
        project2 = TranslationProject(groups={"group2": {"entry2": "value2"}})

        cache.save_project(project1, "project1", "en")
        cache.save_project(project2, "project2", "en")

        assert cache.get_project("project1", "en") is not None
        assert cache.get_project("project2", "en") is not None

    def test_multiple_languages_same_project(self, temp_cache_dir: Path) -> None:
        """Test caching multiple languages for same project."""
        cache = FileCacheProvider(str(temp_cache_dir))
        project_en = TranslationProject(groups={"group1": {"entry1": "Hello"}})
        project_fr = TranslationProject(groups={"group1": {"entry1": "Bonjour"}})

        cache.save_project(project_en, "project1", "en")
        cache.save_project(project_fr, "project1", "fr")

        retrieved_en = cache.get_project("project1", "en")
        retrieved_fr = cache.get_project("project1", "fr")

        assert retrieved_en is not None
        assert retrieved_fr is not None
        assert retrieved_en.groups["group1"]["entry1"] == "Hello"
        assert retrieved_fr.groups["group1"]["entry1"] == "Bonjour"
