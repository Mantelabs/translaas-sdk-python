"""Tests for flat-json project parsing."""

from translaas.client.parsing import translation_project_from_response


class TestFlatJsonProjectParsing:
    def test_composite_keys(self) -> None:
        data = {
            "common.hello": "Hello",
            "common.goodbye": "Bye",
            "project": "p",
            "lang": "en",
        }
        proj = translation_project_from_response(data, format_hint="flat-json")
        assert proj.groups["common"]["hello"] == "Hello"
        assert proj.groups["common"]["goodbye"] == "Bye"

    def test_auto_detect_flat_shape(self) -> None:
        data = {"checkout.title": "Checkout", "checkout.pay": "Pay"}
        proj = translation_project_from_response(data)
        assert "checkout" in proj.groups
        assert proj.groups["checkout"]["title"] == "Checkout"
