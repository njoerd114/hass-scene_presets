from __future__ import annotations
COLOR_MODES = ("xy", "hs", "rgb", "rgbw", "rgbww", "rgbcw")
BRIGHTNESS_MODES = ("brightness", "white")
TEMP_MODE = "color_temp"
WIDE_COLOR_MODES = ("rgbw", "rgbww", "rgbcw")


def supports_color(modes: list[str]) -> bool:
    return any(mode in modes for mode in COLOR_MODES)


def supports_temperature(modes: list[str]) -> bool:
    return TEMP_MODE in modes


def supports_brightness(modes: list[str]) -> bool:
    return any(mode in modes for mode in BRIGHTNESS_MODES)


def _build_color_field(modes, color, rgb, hs, white) -> dict | None:
    if "xy" in modes:
        return {"xy_color": color}

    if "hs" in modes:
        return {"hs_color": hs if hs is not None else color}

    if "rgb" in modes:
        return {"rgb_color": rgb if rgb is not None else color}

    if "rgbw" in modes:
        if white is not None and rgb is not None:
            return {"rgbw_color": tuple([*rgb, white])}
        return {"rgb_color": rgb if rgb is not None else color}

    if "rgbww" in modes or "rgbcw" in modes:
        if white is not None and rgb is not None:
            return {"rgbww_color": tuple([*rgb, white, 0])}
        return {"rgb_color": rgb if rgb is not None else color}

    return None


def build_light_params(
    attributes: dict,
    color: tuple[float, float],
    brightness: int,
    transition: float,
    effect: str | None = None,
    kelvin: int | None = None,
    rgb: tuple[float, float, float] | None = None,
    hs: tuple[float, float] | None = None,
    white: int | None = None,
) -> dict | None:
    modes = attributes.get("supported_color_modes") or []
    params = {"brightness": brightness, "transition": transition}

    color_field = _build_color_field(modes, color, rgb, hs, white)
    if color_field is not None:
        params.update(color_field)
    elif supports_temperature(modes):
        params["color_temp_kelvin"] = kelvin
    elif not supports_brightness(modes):
        return None

    if effect and effect in (attributes.get("effect_list") or []):
        params["effect"] = effect

    return params
