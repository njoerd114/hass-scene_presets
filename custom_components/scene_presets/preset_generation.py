from __future__ import annotations
import hashlib

DEFAULT_CATEGORY_ID = "wled-effects"
DEFAULT_CATEGORY_NAME = "WLED Effects"
DEFAULT_EFFECT_ICON = "mdi:creation"
NEUTRAL_XY = {"x": 0.3127, "y": 0.3290}


def _effect_preset_id(effect):
    digest = hashlib.sha1(effect.encode("utf-8")).hexdigest()[:12]
    return f"wled-effect-{digest}"


def generate_effect_presets(
    effects: list[str],
    category_id: str = DEFAULT_CATEGORY_ID,
    category_name: str = DEFAULT_CATEGORY_NAME,
) -> dict:
    seen = set()
    presets = []

    for effect in effects:
        if not effect or effect in seen:
            continue
        seen.add(effect)

        presets.append(
            {
                "id": _effect_preset_id(effect),
                "categoryId": category_id,
                "name": effect,
                "icon": DEFAULT_EFFECT_ICON,
                "bri": 255,
                "effect": effect,
                "lights": [dict(NEUTRAL_XY)],
                "generated": True,
            }
        )

    return {
        "category": {"id": category_id, "name": category_name},
        "presets": presets,
    }
