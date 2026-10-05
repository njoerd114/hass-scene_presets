from scene_presets.validation import merge_presets, validate_presets

VALID = {
    "presets": [
        {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}]}
    ],
    "categories": [{"id": "c", "name": "C"}],
}


def test_valid_data_passes():
    valid, errors = validate_presets(VALID)

    assert errors == []
    assert len(valid["presets"]) == 1
    assert len(valid["categories"]) == 1


def test_missing_required_fields_are_reported():
    valid, errors = validate_presets({"presets": [{"id": "a"}], "categories": []})

    assert errors
    assert valid["presets"] == []


def test_invalid_xy_is_reported():
    data = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": "nope", "y": 0.2}]}
        ],
        "categories": [],
    }

    valid, errors = validate_presets(data)

    assert errors
    assert valid["presets"] == []


def test_duplicate_ids_are_reported():
    data = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}]},
            {"id": "a", "categoryId": "c", "name": "A2", "lights": [{"x": 0.1, "y": 0.2}]},
        ],
        "categories": [],
    }

    valid, errors = validate_presets(data)

    assert any("duplicate" in error for error in errors)
    assert len(valid["presets"]) == 1


def test_merge_detects_conflicting_custom_id():
    custom = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "Dup", "lights": [{"x": 0.1, "y": 0.2}]}
        ],
        "categories": [],
    }

    merged, errors = merge_presets(VALID, custom)

    assert any("conflicts" in error for error in errors)
    assert len(merged["presets"]) == 1


def test_merge_adds_valid_custom_presets_and_categories():
    custom = {
        "presets": [
            {"id": "b", "categoryId": "d", "name": "B", "lights": [{"x": 0.1, "y": 0.2}]}
        ],
        "categories": [{"id": "d", "name": "D"}],
    }

    merged, errors = merge_presets(VALID, custom)

    assert errors == []
    assert {preset["id"] for preset in merged["presets"]} == {"a", "b"}
    assert {category["id"] for category in merged["categories"]} == {"c", "d"}
    assert all(preset.get("custom") for preset in merged["presets"] if preset["id"] == "b")


def test_merge_keeps_base_intact():
    base = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}]}
        ],
        "categories": [{"id": "c", "name": "C"}],
    }
    custom = {
        "presets": [
            {"id": "b", "categoryId": "c", "name": "B", "lights": [{"x": 0.1, "y": 0.2}]}
        ],
        "categories": [],
    }

    merge_presets(base, custom)

    assert [preset["id"] for preset in base["presets"]] == ["a"]


def test_valid_optional_fields_pass():
    data = {
        "presets": [
            {
                "id": "a",
                "categoryId": "c",
                "name": "A",
                "lights": [{"x": 0.1, "y": 0.2}],
                "white": 200,
                "kelvin": 2700,
                "wled_speed": 128,
                "wled_intensity": 64,
                "distribution": "balanced",
                "transition_style": "instant",
                "effect": "Rainbow",
                "wled_preset": "Xmas",
                "targets": {"entity_id": "light.x"},
            }
        ],
        "categories": [],
    }

    valid, errors = validate_presets(data)

    assert errors == []
    assert len(valid["presets"]) == 1


def test_invalid_optional_numeric_is_rejected():
    data = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}], "white": 999}
        ],
        "categories": [],
    }

    valid, errors = validate_presets(data)

    assert errors
    assert valid["presets"] == []


def test_invalid_distribution_is_rejected():
    data = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}], "distribution": "nope"}
        ],
        "categories": [],
    }

    _, errors = validate_presets(data)

    assert errors


def test_invalid_transition_style_is_rejected():
    data = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}], "transition_style": "nope"}
        ],
        "categories": [],
    }

    _, errors = validate_presets(data)

    assert errors


def test_invalid_targets_is_rejected():
    data = {
        "presets": [
            {"id": "a", "categoryId": "c", "name": "A", "lights": [{"x": 0.1, "y": 0.2}], "targets": "nope"}
        ],
        "categories": [],
    }

    _, errors = validate_presets(data)

    assert errors
