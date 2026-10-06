from scene_presets.color_conversion import xy_to_hs, xy_to_rgb


def test_xy_to_rgb_returns_three_channels():
    result = xy_to_rgb((0.4, 0.4))

    assert len(result) == 3


def test_xy_to_rgb_accepts_a_two_argument_ha_call():
    # HA's color_xy_to_RGB(vX, vY, Gamut=None) must be called without a brightness
    # positional argument, otherwise 255 is interpreted as the Gamut.
    assert xy_to_rgb((0.1, 0.3)) == (round(255 * 0.1 / 0.4), round(255 * 0.3 / 0.4), 0)


def test_xy_to_hs_returns_hue_and_saturation():
    assert len(xy_to_hs((0.4, 0.4))) == 2
