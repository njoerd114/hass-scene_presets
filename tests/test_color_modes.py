from scene_presets.color_modes import build_light_params


def _attrs(modes, effect_list=None):
    attributes = {"supported_color_modes": modes}
    if effect_list is not None:
        attributes["effect_list"] = effect_list
    return attributes


def test_xy_light_gets_xy_color_and_scalars():
    params = build_light_params(_attrs(["xy"]), (0.4, 0.4), 100, 1)

    assert params["xy_color"] == (0.4, 0.4)
    assert params["brightness"] == 100
    assert params["transition"] == 1


def test_hs_light_gets_hs_color():
    params = build_light_params(_attrs(["hs"]), (0.4, 0.4), 100, 1, hs=(120.0, 50.0))

    assert params["hs_color"] == (120.0, 50.0)
    assert "xy_color" not in params


def test_hs_light_falls_back_to_color_when_hs_missing():
    params = build_light_params(_attrs(["hs"]), (0.4, 0.4), 100, 1)

    assert params["hs_color"] == (0.4, 0.4)


def test_rgb_light_gets_rgb_color():
    params = build_light_params(_attrs(["rgb"]), (0.4, 0.4), 100, 1, rgb=(10, 20, 30))

    assert params["rgb_color"] == (10, 20, 30)


def test_rgbw_light_gets_rgbw_color_when_white_provided():
    params = build_light_params(_attrs(["rgbw"]), (0.4, 0.4), 100, 1, rgb=(10, 20, 30), white=200)

    assert params["rgbw_color"] == (10, 20, 30, 200)


def test_rgbw_light_falls_back_to_rgb_without_white():
    params = build_light_params(_attrs(["rgbw"]), (0.4, 0.4), 100, 1, rgb=(10, 20, 30))

    assert params["rgb_color"] == (10, 20, 30)


def test_rgbww_light_gets_rgbww_color_when_white_provided():
    params = build_light_params(_attrs(["rgbww"]), (0.4, 0.4), 100, 1, rgb=(10, 20, 30), white=200)

    assert params["rgbww_color"] == (10, 20, 30, 200, 0)


def test_color_temp_light_uses_the_provided_kelvin():
    params = build_light_params(_attrs(["color_temp"]), (0.4, 0.4), 100, 1, kelvin=2700)

    assert params["color_temp_kelvin"] == 2700
    assert "xy_color" not in params


def test_white_light_gets_brightness_only():
    params = build_light_params(_attrs(["white"]), (0.4, 0.4), 100, 1)

    assert params["brightness"] == 100
    assert "xy_color" not in params
    assert "color_temp_kelvin" not in params


def test_brightness_light_gets_brightness_only():
    params = build_light_params(_attrs(["brightness"]), (0.4, 0.4), 100, 1)

    assert params["brightness"] == 100
    assert "xy_color" not in params


def test_onoff_light_is_unsupported():
    assert build_light_params(_attrs(["onoff"]), (0.4, 0.4), 100, 1) is None


def test_missing_or_none_modes_is_unsupported():
    assert build_light_params({}, (0.4, 0.4), 100, 1) is None
    assert build_light_params({"supported_color_modes": None}, (0.4, 0.4), 100, 1) is None


def test_effect_is_applied_only_when_supported():
    supported = build_light_params(_attrs(["xy"], ["Rainbow"]), (0.4, 0.4), 100, 1, effect="Rainbow")
    assert supported["effect"] == "Rainbow"

    unknown = build_light_params(_attrs(["xy"], ["Meteor"]), (0.4, 0.4), 100, 1, effect="Rainbow")
    assert "effect" not in unknown

    no_list = build_light_params(_attrs(["xy"]), (0.4, 0.4), 100, 1, effect="Rainbow")
    assert "effect" not in no_list

    none = build_light_params(_attrs(["xy"], ["Rainbow"]), (0.4, 0.4), 100, 1, effect=None)
    assert "effect" not in none
