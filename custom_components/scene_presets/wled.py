from __future__ import annotations
import asyncio
from typing import Any

PRESET_SELECT_DOMAIN = "select"
PRESET_TRANSLATION_KEY = "preset"


def select_preset_entity_ids(registry: Any, entries_for_device: Any, light_entity_ids: list[str]) -> list[str]:
    selected = []
    seen = set()

    for light_entity_id in light_entity_ids:
        entry = registry.async_get(light_entity_id)
        if entry is None or entry.device_id is None:
            continue

        for candidate in entries_for_device(registry, entry.device_id):
            if candidate.entity_id in seen:
                continue
            if candidate.domain != PRESET_SELECT_DOMAIN:
                continue
            if getattr(candidate, "translation_key", None) != PRESET_TRANSLATION_KEY:
                continue

            seen.add(candidate.entity_id)
            selected.append(candidate.entity_id)

    return selected


async def apply_wled_preset(hass: Any, light_entity_ids: list[str], preset_name: str) -> None:
    from homeassistant.helpers import entity_registry

    registry = entity_registry.async_get(hass)
    preset_entity_ids = select_preset_entity_ids(
        registry,
        entity_registry.async_entries_for_device,
        light_entity_ids,
    )

    tasks = []
    for entity_id in preset_entity_ids:
        state = hass.states.get(entity_id)
        options = (state.attributes.get("options") or []) if state else []
        if preset_name not in options:
            continue

        tasks.append(
            hass.services.async_call(
                "select",
                "select_option",
                {"entity_id": entity_id, "option": preset_name},
                blocking=False,
            )
        )

    if tasks:
        await asyncio.gather(*tasks)


def _segment_prefix_suffix(unique_id: str | None) -> tuple[str, str] | None:
    if not unique_id:
        return None

    prefix, sep, suffix = unique_id.rpartition("_")
    if not sep or not suffix.isdigit():
        return None

    return prefix, suffix


def resolve_wled_controls(registry: Any, entries_for_device: Any, light_entity_ids: list[str]) -> list[dict]:
    controls = []

    for light_entity_id in light_entity_ids:
        entry = registry.async_get(light_entity_id)
        if entry is None or entry.device_id is None:
            continue

        unique_id = getattr(entry, "unique_id", None)
        parsed = _segment_prefix_suffix(unique_id)
        if parsed is None:
            if not unique_id:
                continue
            prefix, suffix = unique_id, "0"
        else:
            prefix, suffix = parsed
        siblings = {
            candidate.unique_id: candidate
            for candidate in entries_for_device(registry, entry.device_id)
            if getattr(candidate, "unique_id", None)
        }

        palette = siblings.get(f"{prefix}_palette_{suffix}")
        speed = siblings.get(f"{prefix}_speed_{suffix}")
        intensity = siblings.get(f"{prefix}_intensity_{suffix}")

        if palette is None and speed is None and intensity is None:
            continue

        controls.append(
            {
                "palette": palette.entity_id if palette else None,
                "speed": speed.entity_id if speed else None,
                "intensity": intensity.entity_id if intensity else None,
            }
        )

    return controls


async def apply_wled_controls(hass: Any, light_entity_ids: list[str], palette: str | None = None, speed: int | None = None, intensity: int | None = None) -> None:
    from homeassistant.helpers import entity_registry

    registry = entity_registry.async_get(hass)
    controls = resolve_wled_controls(
        registry,
        entity_registry.async_entries_for_device,
        light_entity_ids,
    )

    tasks = []
    for control in controls:
        if palette is not None and control["palette"]:
            state = hass.states.get(control["palette"])
            options = (state.attributes.get("options") or []) if state else []
            if palette in options:
                tasks.append(
                    hass.services.async_call(
                        "select",
                        "select_option",
                        {"entity_id": control["palette"], "option": palette},
                        blocking=False,
                    )
                )

        if speed is not None and control["speed"]:
            tasks.append(
                hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": control["speed"], "value": speed},
                    blocking=False,
                )
            )

        if intensity is not None and control["intensity"]:
            tasks.append(
                hass.services.async_call(
                    "number",
                    "set_value",
                    {"entity_id": control["intensity"], "value": intensity},
                    blocking=False,
                )
            )

    if tasks:
        await asyncio.gather(*tasks)
