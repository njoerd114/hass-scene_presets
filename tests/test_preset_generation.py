from scene_presets.preset_generation import generate_effect_presets


def test_generates_one_preset_per_unique_effect():
    result = generate_effect_presets(["Rainbow", "Fire"], "cat")

    assert result["category"] == {"id": "cat", "name": "WLED Effects"}
    assert [preset["name"] for preset in result["presets"]] == ["Rainbow", "Fire"]
    assert all(preset["effect"] in {"Rainbow", "Fire"} for preset in result["presets"])


def test_deduplicates_effects():
    result = generate_effect_presets(["Rainbow", "Rainbow", "Fire"], "cat")

    assert len(result["presets"]) == 2


def test_ids_are_deterministic_and_unique():
    first = generate_effect_presets(["Rainbow", "Fire"], "cat")
    second = generate_effect_presets(["Rainbow", "Fire"], "cat")

    ids = [preset["id"] for preset in first["presets"]]
    assert ids == [preset["id"] for preset in second["presets"]]
    assert len(set(ids)) == len(ids)


def test_generated_presets_validate():
    from scene_presets.validation import validate_presets

    result = generate_effect_presets(["Rainbow"], "cat")
    valid, errors = validate_presets({"presets": result["presets"], "categories": [result["category"]]})

    assert errors == []
    assert len(valid["presets"]) == 1
