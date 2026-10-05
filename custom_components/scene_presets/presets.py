from __future__ import annotations

import voluptuous as vol
import asyncio
import logging
from typing import Any
from .file_utils import PRESET_DATA
from .color_management import *
from .color_temperature import find_closest_ct_match
from .color_modes import build_light_params
from .color_conversion import xy_to_hs, xy_to_rgb
from .transitions import DEFAULT_TRANSITION_STEPS, EASING_STYLES, interpolate

_LOGGER = logging.getLogger(__name__)


async def _ease_light(hass, entity_id, hass_state, base_params, target_color, target_brightness, duration, style):
    steps = DEFAULT_TRANSITION_STEPS
    step_transition = duration / steps
    current_brightness = hass_state.attributes.get("brightness") or target_brightness
    brightness_steps = interpolate(current_brightness, target_brightness, steps, style)

    color_key = "xy_color" if "xy_color" in base_params else ("hs_color" if "hs_color" in base_params else None)
    color_steps = None
    if color_key == "xy_color":
        current_color = hass_state.attributes.get("xy_color")
        if isinstance(current_color, (list, tuple)) and len(current_color) == 2:
            first = interpolate(current_color[0], target_color[0], steps, style)
            second = interpolate(current_color[1], target_color[1], steps, style)
            color_steps = list(zip(first, second))

    for index in range(steps):
        params = dict(base_params)
        params["entity_id"] = entity_id
        params["transition"] = step_transition
        params["brightness"] = max(0, round(brightness_steps[index]))
        if color_steps is not None:
            params[color_key] = color_steps[index]
        await hass.services.async_call("light", "turn_on", params, blocking=True)


async def apply_preset(
    hass: Any,
    preset_id: str,
    light_entity_ids: list[str],
    transition: float,
    shuffle: bool,
    smart_shuffle: bool,
    brightness_override: int | None = None,
    effect_override: str | None = None,
    wled_preset_override: str | None = None,
    wled_palette_override: str | None = None,
    wled_speed_override: int | None = None,
    wled_intensity_override: int | None = None,
    distribution_override: str | None = None,
    transition_style_override: str | None = None
) -> None:
    preset_data = None
    for preset in PRESET_DATA.get("presets", []):
        if preset.get("id") == preset_id:
            preset_data = preset
            break

    if not preset_data:
        raise vol.Invalid(f"Preset '{preset_id}' not found.")

    brightness = brightness_override if brightness_override is not None else preset_data.get("bri", 255)

    effect = effect_override if effect_override is not None else preset_data.get("effect")

    wled_preset = wled_preset_override if wled_preset_override is not None else preset_data.get("wled_preset")

    wled_palette = wled_palette_override if wled_palette_override is not None else preset_data.get("wled_palette")
    wled_speed = wled_speed_override if wled_speed_override is not None else preset_data.get("wled_speed")
    wled_intensity = wled_intensity_override if wled_intensity_override is not None else preset_data.get("wled_intensity")

    preset_kelvin = preset_data.get("kelvin")

    preset_white = preset_data.get("white")

    distribution = distribution_override if distribution_override is not None else preset_data.get("distribution", "sequence")
    transition_style = transition_style_override if transition_style_override is not None else preset_data.get("transition_style", "fade")
    if transition_style == "instant":
        transition = 0

    preset_colors = [(light["x"], light["y"]) for light in preset_data["lights"]]

    randomized_colors = None
    assigned_colors = None
    if shuffle:
        randomized_colors = get_randomized_colors(preset_colors, len(light_entity_ids))
    else:
        assigned_colors = assign_colors(preset_colors, len(light_entity_ids), distribution)

    tasks = []

    for index, entity_id in enumerate(light_entity_ids):
        hass_state = hass.states.get(entity_id)
        if not hass_state:
            continue

        if shuffle:
            current_color = hass_state.attributes.get("xy_color", None)

            if current_color is not None and smart_shuffle:
                next_color = get_next_smart_random_color(current_color, preset_colors)
            elif randomized_colors is not None and index < len(randomized_colors):
                next_color = randomized_colors[index]
            else:
                next_color = get_random_color(preset_colors)
        else:
            next_color = assigned_colors[index] if index < len(assigned_colors) else get_next_color(index, preset_colors)

        kelvin = preset_kelvin if preset_kelvin is not None else find_closest_ct_match(next_color[0], next_color[1])

        light_params = build_light_params(
            hass_state.attributes,
            next_color,
            brightness,
            transition,
            effect,
            kelvin,
            xy_to_rgb(next_color),
            xy_to_hs(next_color),
            preset_white,
        )
        if light_params is None:
            continue

        if transition_style in EASING_STYLES and transition and transition > 0:
            tasks.append(
                _ease_light(
                    hass,
                    entity_id,
                    hass_state,
                    light_params,
                    next_color,
                    brightness,
                    transition,
                    transition_style,
                )
            )
            continue

        light_params["entity_id"] = entity_id
        tasks.append(
            hass.services.async_call(
                "light",
                "turn_on",
                light_params,
                blocking=False,
            )
        )

    await asyncio.gather(*tasks)

    if wled_preset:
        from .wled import apply_wled_preset

        await apply_wled_preset(hass, light_entity_ids, wled_preset)

    if wled_palette is not None or wled_speed is not None or wled_intensity is not None:
        from .wled import apply_wled_controls

        await apply_wled_controls(hass, light_entity_ids, wled_palette, wled_speed, wled_intensity)
