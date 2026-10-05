from scene_presets.preset_authoring import (
    build_preset,
    ensure_category,
    find_category_id,
    is_allowed_image,
    remove_preset,
    sanitize_filename,
    upsert_preset,
)


def test_sanitize_filename_strips_unsafe_characters():
    assert sanitize_filename("My Cool Preset!!.png") == "My-Cool-Preset-.png"
    assert sanitize_filename("../../etc/passwd") == "etc-passwd"


def test_is_allowed_image():
    assert is_allowed_image("photo.PNG")
    assert is_allowed_image("a.jpeg")
    assert not is_allowed_image("script.sh")
    assert not is_allowed_image("noextension")


def test_ensure_category_creates_then_finds():
    data = {"presets": [], "categories": []}

    first = ensure_category(data, "My Presets")
    second = ensure_category(data, "My Presets")

    assert first == second
    assert len(data["categories"]) == 1
    assert find_category_id(data, "My Presets") == first


def test_upsert_preset_appends_and_replaces():
    data = {"presets": [], "categories": []}
    preset = build_preset("A", [{"x": 0.1, "y": 0.2}], "c")

    upsert_preset(data, preset)
    assert len(data["presets"]) == 1

    preset["name"] = "A2"
    upsert_preset(data, preset)

    assert len(data["presets"]) == 1
    assert data["presets"][0]["name"] == "A2"


def test_remove_preset():
    data = {"presets": [build_preset("A", [{"x": 0.1, "y": 0.2}], "c")], "categories": []}
    preset_id = data["presets"][0]["id"]

    assert remove_preset(data, preset_id) is True
    assert data["presets"] == []
    assert remove_preset(data, preset_id) is False


def test_build_preset_normalizes_colors_and_optional_fields():
    preset = build_preset(
        "A",
        [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}],
        "c",
        brightness=120,
        image="custom.png",
        effect="Rainbow",
        kelvin=2700,
    )

    assert preset["lights"] == [{"x": 0.1, "y": 0.2}, {"x": 0.3, "y": 0.4}]
    assert preset["bri"] == 120
    assert preset["img"] == "custom.png"
    assert preset["effect"] == "Rainbow"
    assert preset["kelvin"] == 2700
    assert "white" not in preset
