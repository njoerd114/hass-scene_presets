import json

from scene_presets.portability import decode_share, encode_share, export_custom_presets, parse_import

CUSTOM = {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}], "custom": True}
BUILTIN = {"id": "b", "categoryId": "c", "name": "B", "lights": [{"x": 0.1, "y": 0.2}]}


def test_export_includes_only_custom_presets():
    exported = export_custom_presets([CUSTOM, BUILTIN])

    assert '"a"' in exported
    assert '"b"' not in exported


def test_export_includes_referenced_categories():
    categories = [
        {"id": "c", "name": "C", "custom": True},
        {"id": "unused", "name": "Unused"},
    ]

    exported = json.loads(export_custom_presets([CUSTOM, BUILTIN], categories))

    assert [category["id"] for category in exported["categories"]] == ["c"]


def test_share_code_round_trips():
    payload = export_custom_presets([CUSTOM])

    assert decode_share(encode_share(payload)) == payload


def test_parse_import_accepts_json_string():
    valid, errors = parse_import(export_custom_presets([CUSTOM]))

    assert errors == []
    assert len(valid["presets"]) == 1


def test_parse_import_accepts_share_code():
    code = encode_share(export_custom_presets([CUSTOM]))

    valid, errors = parse_import(code)

    assert errors == []
    assert valid["presets"][0]["id"] == "a"


def test_parse_import_accepts_dict():
    valid, errors = parse_import({"presets": [CUSTOM], "categories": []})

    assert errors == []
    assert len(valid["presets"]) == 1


def test_parse_import_reports_invalid_payload():
    valid, errors = parse_import("!!!not json or base64!!!")

    assert errors
    assert valid["presets"] == []


def test_parse_import_reports_malformed_json_object():
    valid, errors = parse_import('{"presets": [{"id": "a"}]}')

    assert errors
