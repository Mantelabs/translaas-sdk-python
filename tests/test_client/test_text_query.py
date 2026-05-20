"""Tests for text endpoint query building."""

from translaas.client.text_query import build_text_query_params, merge_number_into_parameters


class TestTextQuery:
    def test_injects_n_uppercase(self) -> None:
        merged = merge_number_into_parameters(1.5, {"name": "x"})
        assert merged is not None
        assert merged["N"] == "1.5"
        assert merged["name"] == "x"

    def test_build_text_query_includes_n_and_N(self) -> None:
        params = build_text_query_params(
            group="g",
            entry="e",
            lang="en",
            number=2,
            parameters={"foo": "bar"},
        )
        assert params["n"] == "2"
        assert params["N"] == "2"
        assert params["foo"] == "bar"
