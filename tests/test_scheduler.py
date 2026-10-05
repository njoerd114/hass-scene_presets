from scene_presets.scheduler import circadian_command


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
