from datetime import datetime, timedelta

from scene_presets.circadian import brightness_pct, color_temp_kelvin, sun_position

NOON = datetime(2026, 6, 1, 13, 0, 0)
MIDNIGHT = datetime(2026, 6, 1, 1, 0, 0)
SUNRISE = datetime(2026, 6, 1, 6, 0, 0)
SUNSET = datetime(2026, 6, 1, 20, 0, 0)


def test_color_temp_is_max_at_solar_noon():
    assert color_temp_kelvin(1.0) == 6500


def test_color_temp_is_min_at_horizon():
    assert color_temp_kelvin(0.0) == 3000


def test_color_temp_is_sleep_temp_at_deep_night():
    assert color_temp_kelvin(-1.0) == 1900


def test_color_temp_is_rounded_to_five_kelvin():
    assert color_temp_kelvin(0.5) % 5 == 0
    assert color_temp_kelvin(-0.5) % 5 == 0


def test_brightness_is_max_during_day():
    assert brightness_pct(0.5, 10, 100) == 100


def test_brightness_is_min_at_deep_night():
    assert brightness_pct(-1.0, 10, 100) == 10


def test_sun_position_is_positive_at_noon():
    position = sun_position(NOON, SUNRISE, SUNSET, NOON, MIDNIGHT)

    assert position == 1.0


def test_sun_position_is_zero_at_sunrise():
    assert sun_position(SUNRISE, SUNRISE, SUNSET, NOON, MIDNIGHT) == 0.0


def test_sun_position_is_negative_at_midnight():
    position = sun_position(MIDNIGHT, SUNRISE, SUNSET, NOON, MIDNIGHT)

    assert position == -1.0


def test_sun_position_mid_morning_is_between_zero_and_one():
    mid_morning = SUNRISE + timedelta(hours=2)
    position = sun_position(mid_morning, SUNRISE, SUNSET, NOON, MIDNIGHT)

    assert 0.0 < position < 1.0
