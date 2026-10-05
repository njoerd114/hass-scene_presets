from __future__ import annotations
DEFAULT_MIN_KELVIN = 3000
DEFAULT_MAX_KELVIN = 6500
DEFAULT_SLEEP_KELVIN = 1900
DEFAULT_MIN_BRIGHTNESS = 1
DEFAULT_MAX_BRIGHTNESS = 100


def color_temp_kelvin(
    position: float,
    min_kelvin: int = DEFAULT_MIN_KELVIN,
    max_kelvin: int = DEFAULT_MAX_KELVIN,
    sleep_kelvin: int = DEFAULT_SLEEP_KELVIN,
) -> int:
    if position > 0:
        kelvin = (max_kelvin - min_kelvin) * position + min_kelvin
    elif position == 0:
        kelvin = min_kelvin
    else:
        kelvin = abs(min_kelvin - sleep_kelvin) * (1 + position) + sleep_kelvin

    return 5 * round(kelvin / 5)


def brightness_pct(
    position: float,
    min_brightness: int = DEFAULT_MIN_BRIGHTNESS,
    max_brightness: int = DEFAULT_MAX_BRIGHTNESS,
) -> int:
    if position > 0:
        return max_brightness

    return round((max_brightness - min_brightness) * (1 + position) + min_brightness)


def elevation_to_position(elevation: float, low: float = -18.0, high: float = 90.0) -> float:
    if high <= low:
        return 0.0

    return max(-1.0, min(1.0, 2 * (elevation - low) / (high - low) - 1))


def sun_position(now, sunrise, sunset, noon, midnight) -> float:
    if sunrise <= now <= sunset:
        half_day = (sunset - sunrise).total_seconds() / 2
        if half_day <= 0:
            return 1.0
        return 1 - abs((now - noon).total_seconds()) / half_day

    if now > sunset:
        night_length = (midnight - sunset).total_seconds()
        if night_length <= 0:
            return -1.0
        return -((now - sunset).total_seconds() / night_length)

    night_length = (sunrise - midnight).total_seconds()
    if night_length <= 0:
        return -1.0
    return -((sunrise - now).total_seconds() / night_length)
