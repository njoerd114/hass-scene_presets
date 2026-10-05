from scene_presets import util


def test_resolve_targets_preserves_order_and_dedupes(monkeypatch):
    monkeypatch.setattr(util.entity_registry, "async_get", lambda hass: object(), raising=False)
    monkeypatch.setattr(util.device_registry, "async_get", lambda hass: object(), raising=False)
    monkeypatch.setattr(util.area_registry, "async_get", lambda hass: object(), raising=False)

    mapping = {
        "light.a": ["light.z", "light.a"],
        "light.b": ["light.a", "light.m"],
    }
    monkeypatch.setattr(
        util,
        "resolve_entity_ids",
        lambda hass, entity_id, depth=0: mapping.get(entity_id, []),
    )

    result = util.resolve_targets(object(), ["light.a", "light.b"], [], [], [], [])

    assert result == ["light.z", "light.a", "light.m"]
