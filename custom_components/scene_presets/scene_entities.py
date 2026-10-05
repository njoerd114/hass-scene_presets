from __future__ import annotations
DEFAULT_SCENE_ICON = "mdi:palette"


def build_scene_definitions(presets: list[dict], default_targets: dict | None = None) -> list[dict]:
    definitions = []

    for preset in presets:
        preset_id = preset.get("id")
        if not preset_id:
            continue

        targets = preset.get("targets") or default_targets

        definitions.append(
            {
                "unique_id": f"scene_presets_{preset_id}",
                "name": preset.get("name") or preset_id,
                "icon": preset.get("icon") or DEFAULT_SCENE_ICON,
                "preset_id": preset_id,
                "targets": targets,
                "available": bool(targets),
            }
        )

    return definitions
