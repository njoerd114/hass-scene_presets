from types import SimpleNamespace

from scene_presets.scheduler import (
    SceneScheduler,
    adaptive_lighting_command,
    circadian_command,
)


def test_full_day_position_gives_max_kelvin_and_brightness():
    command = circadian_command({}, 1.0)

    assert command["color_temp_kelvin"] == 6500
    assert command["brightness"] == 255


def test_deep_night_position_gives_sleep_kelvin_and_min_brightness():
    command = circadian_command({}, -1.0)

    assert command["color_temp_kelvin"] == 1900
    assert command["brightness"] >= 1


def test_custom_ranges_are_respected():
    command = circadian_command(
        {"min_kelvin": 2200, "max_kelvin": 5000, "sleep_kelvin": 1500}, 1.0
    )

    assert command["color_temp_kelvin"] == 5000


def test_brightness_is_clamped_to_a_minimum_of_one():
    command = circadian_command({"min_brightness": 0, "max_brightness": 100}, -1.0)

    assert command["brightness"] >= 1


def test_elevation_to_position_bounds():
    from scene_presets.circadian import elevation_to_position

    assert elevation_to_position(-18.0) == -1.0
    assert elevation_to_position(90.0) == 1.0
    assert elevation_to_position(36.0) == 0.0


def test_adaptive_lighting_command_maps_switch_attributes():
    state = SimpleNamespace(
        state="on",
        attributes={"color_temp_kelvin": 4000, "brightness_pct": 50.0},
    )

    command = adaptive_lighting_command(state)

    assert command == {"color_temp_kelvin": 4000, "brightness": 128}


def test_adaptive_lighting_command_returns_none_without_available_attributes():
    off_state = SimpleNamespace(
        state="off",
        attributes={"color_temp_kelvin": 4000, "brightness_pct": 50.0},
    )
    missing_attributes = SimpleNamespace(state="on", attributes={})

    assert adaptive_lighting_command(None) is None
    assert adaptive_lighting_command(off_state) is None
    assert adaptive_lighting_command(missing_attributes) is None


def test_scene_scheduler_uses_adaptive_lighting_command_when_switch_is_on():
    states = {
        "switch.adaptive_lighting_living_room": SimpleNamespace(
            state="on",
            attributes={"color_temp_kelvin": 4100, "brightness_pct": 25.0},
        ),
        "sun.sun": SimpleNamespace(attributes={"elevation": 90.0}),
    }
    scheduler = SceneScheduler(SimpleNamespace(states=SimpleNamespace(get=states.get)))
    scheduler._config = {
        "adaptive_lighting_switch": "switch.adaptive_lighting_living_room",
        "light_entity_ids": ["light.living_room"],
    }

    command = scheduler._command()

    assert command == {"color_temp_kelvin": 4100, "brightness": 64}


def test_scene_scheduler_falls_back_when_adaptive_lighting_switch_is_off():
    states = {
        "switch.adaptive_lighting_living_room": SimpleNamespace(
            state="off",
            attributes={"color_temp_kelvin": None, "brightness_pct": None},
        ),
        "sun.sun": SimpleNamespace(attributes={"elevation": 90.0}),
    }
    scheduler = SceneScheduler(SimpleNamespace(states=SimpleNamespace(get=states.get)))
    scheduler._config = {
        "adaptive_lighting_switch": "switch.adaptive_lighting_living_room",
        "light_entity_ids": ["light.living_room"],
    }

    command = scheduler._command()

    assert "color_temp_kelvin" in command
    assert "brightness" in command
