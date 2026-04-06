"""Unit tests for ``translaas.client.parsing``."""

import pytest

from translaas.client.parsing import (
    project_locales_from_response,
    translation_group_from_response,
    translation_project_from_response,
)
from translaas.exceptions import TranslaasApiException


class TestTranslationGroupFromResponse:
    def test_structured_entries_and_entry_context(self) -> None:
        data = {
            "project": "p",
            "lang": "en",
            "version": 2,
            "generatedAt": "2024-01-01T00:00:00Z",
            "entries": {"a": "A"},
            "entryContext": {"a": {"note": "x"}},
        }
        g = translation_group_from_response(data)
        assert g.entries == {"a": "A"}
        assert g.version == 2
        assert g.generated_at == "2024-01-01T00:00:00Z"
        assert g.project == "p"
        assert g.lang == "en"
        assert g.entry_context == {"a": {"note": "x"}}

    def test_flat_json_map(self) -> None:
        """``format=flat-json`` style map (entry key -> string)."""
        data = {"hello": "world", "foo": "bar"}
        g = translation_group_from_response(data)
        assert g.entries == data
        assert g.entry_context is None
        assert g.version is None

    def test_version_non_int_becomes_none(self) -> None:
        data = {"entries": {"k": "v"}, "version": "nope"}
        g = translation_group_from_response(data)
        assert g.version is None

    def test_invalid_not_dict(self) -> None:
        with pytest.raises(TranslaasApiException, match="expected object"):
            translation_group_from_response([])


class TestTranslationProjectFromResponse:
    def test_nested_groups_shape(self) -> None:
        data = {
            "groups": {"g1": {"e": "v"}},
            "groupEntryContext": {"g1": {"e": {"ctx": "1"}}},
        }
        p = translation_project_from_response(data)
        assert p.groups == {"g1": {"e": "v"}}
        assert p.group_entry_context == {"g1": {"e": {"ctx": "1"}}}

    def test_legacy_root_map(self) -> None:
        """Flat group map at root (metadata keys stripped)."""
        data = {"group1": {"a": "1"}, "group2": {"b": "2"}}
        p = translation_project_from_response(data)
        assert p.groups == data
        assert p.group_entry_context is None

    def test_invalid_not_dict(self) -> None:
        with pytest.raises(TranslaasApiException, match="expected object"):
            translation_project_from_response("x")


class TestProjectLocalesFromResponse:
    def test_object_with_locales(self) -> None:
        data = {
            "locales": ["en", "fr"],
            "project": "p1",
            "lastModifiedUtc": "2024-06-01T12:00:00Z",
        }
        pl = project_locales_from_response(data)
        assert pl.locales == ["en", "fr"]
        assert pl.project == "p1"
        assert pl.last_modified_utc == "2024-06-01T12:00:00Z"

    def test_plain_list(self) -> None:
        pl = project_locales_from_response(["de", "it"])
        assert pl.locales == ["de", "it"]

    def test_list_non_string_rejected(self) -> None:
        with pytest.raises(TranslaasApiException, match="must be strings"):
            project_locales_from_response(["en", 1])

    def test_object_locales_not_list(self) -> None:
        with pytest.raises(TranslaasApiException, match="expected list"):
            project_locales_from_response({"locales": "bad"})

    def test_object_locale_items_not_strings(self) -> None:
        with pytest.raises(TranslaasApiException, match="locale codes must be strings"):
            project_locales_from_response({"locales": ["en", None]})

    def test_invalid_top_level(self) -> None:
        with pytest.raises(TranslaasApiException, match="expected dict with 'locales' or list"):
            project_locales_from_response(42)
