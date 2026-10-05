import random

from scene_presets.selection import pick_random_preset

PRESETS = [
    {"id": "a", "categoryId": "c1", "name": "A"},
    {"id": "b", "categoryId": "c1", "name": "B"},
    {"id": "c", "categoryId": "c2", "name": "C"},
]


def test_pick_random_preset_within_category():
    picked = pick_random_preset(PRESETS, "c1", random.Random(1))

    assert picked["id"] in {"a", "b"}


def test_pick_random_preset_any_category_when_none():
    picked = pick_random_preset(PRESETS, None, random.Random(1))

    assert picked["id"] in {"a", "b", "c"}


def test_pick_random_preset_empty_category_returns_none():
    assert pick_random_preset(PRESETS, "nope", random.Random(1)) is None


def test_pick_random_preset_empty_list_returns_none():
    assert pick_random_preset([], None, random.Random(1)) is None


def test_pick_random_preset_is_deterministic_for_a_seed():
    first = pick_random_preset(PRESETS, None, random.Random(42))
    second = pick_random_preset(PRESETS, None, random.Random(42))

    assert first["id"] == second["id"]
