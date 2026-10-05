from scene_presets.prefs import DEFAULT_PREFS, merge_prefs, normalize_prefs


def test_normalize_returns_defaults_for_non_dict():
    assert normalize_prefs(None) == DEFAULT_PREFS
    assert normalize_prefs([]) == DEFAULT_PREFS


def test_normalize_filters_bad_favorites_and_types():
    normalized = normalize_prefs(
        {"favorites": ["a", 1, "b"], "targets": "nope", "tunables": [1, 2]}
    )

    assert normalized == {"favorites": ["a", "b"], "targets": {}, "tunables": {}}


def test_merge_overrides_only_provided_keys():
    current = {"favorites": ["a"], "targets": {"entity_id": "light.x"}, "tunables": {"shuffle": True}}
    updated = merge_prefs(current, {"favorites": ["b", "c"]})

    assert updated["favorites"] == ["b", "c"]
    assert updated["targets"] == {"entity_id": "light.x"}
    assert updated["tunables"] == {"shuffle": True}


def test_merge_normalizes_updates():
    updated = merge_prefs(DEFAULT_PREFS, {"targets": "bad"})

    assert updated["targets"] == {}


def test_normalize_does_not_share_mutable_defaults():
    first = normalize_prefs(None)
    first["favorites"].append("x")

    assert normalize_prefs(None)["favorites"] == []
