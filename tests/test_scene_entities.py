from scene_presets.scene_entities import build_scene_definitions


def test_every_preset_produces_a_scene_definition():
    presets = [
        {"id": "a", "name": "A"},
        {"id": "b", "name": "B", "targets": {"entity_id": "light.x"}},
    ]

    definitions = build_scene_definitions(presets)

    assert [definition["preset_id"] for definition in definitions] == ["a", "b"]


def test_preset_targets_win_over_defaults():
    definitions = build_scene_definitions(
        [{"id": "a", "name": "A", "targets": {"entity_id": "light.x"}}],
        {"entity_id": "light.default"},
    )

    assert definitions[0]["targets"] == {"entity_id": "light.x"}
    assert definitions[0]["available"] is True


def test_targetless_preset_uses_default_targets():
    definitions = build_scene_definitions([{"id": "a", "name": "A"}], {"entity_id": "light.default"})

    assert definitions[0]["targets"] == {"entity_id": "light.default"}
    assert definitions[0]["available"] is True


def test_targetless_preset_without_default_is_unavailable():
    definitions = build_scene_definitions([{"id": "a", "name": "A"}])

    assert definitions[0]["targets"] is None
    assert definitions[0]["available"] is False


def test_custom_icon_and_missing_name_fallbacks():
    definitions = build_scene_definitions([{"id": "a", "icon": "mdi:star"}, {"id": "b"}])

    assert definitions[0]["icon"] == "mdi:star"
    assert definitions[0]["name"] == "a"
    assert definitions[1]["name"] == "b"
    assert definitions[1]["icon"] == "mdi:palette"


def test_preset_without_id_is_skipped():
    assert build_scene_definitions([{"name": "no id"}]) == []
