from __future__ import annotations

REQUIRED_PRESET_FIELDS = ("id", "categoryId", "name", "lights")
VALID_DISTRIBUTIONS = {"sequence", "balanced", "random"}
VALID_TRANSITION_STYLES = {"fade", "instant", "ease_in", "ease_out", "ease_in_out"}
_INT_RANGES = {"white": (0, 255), "kelvin": (1000, 10000), "wled_speed": (0, 255), "wled_intensity": (0, 255)}
_STRING_FIELDS = ("effect", "wled_preset", "wled_palette")


def _is_xy_color(color):
    return (
        isinstance(color, dict)
        and isinstance(color.get("x"), (int, float))
        and isinstance(color.get("y"), (int, float))
    )


def _is_int_in_range(value, low, high):
    return isinstance(value, int) and not isinstance(value, bool) and low <= value <= high


def _validate_optional_fields(preset, label):
    errors = []

    for field, (low, high) in _INT_RANGES.items():
        if field in preset and not _is_int_in_range(preset[field], low, high):
            errors.append(f"preset {label} has invalid {field}")

    if "distribution" in preset and preset["distribution"] not in VALID_DISTRIBUTIONS:
        errors.append(f"preset {label} has invalid distribution")

    if "transition_style" in preset and preset["transition_style"] not in VALID_TRANSITION_STYLES:
        errors.append(f"preset {label} has invalid transition_style")

    for field in _STRING_FIELDS:
        if field in preset and not isinstance(preset[field], str):
            errors.append(f"preset {label} has invalid {field}")

    if "targets" in preset and not isinstance(preset["targets"], dict):
        errors.append(f"preset {label} has invalid targets")

    return errors


def validate_presets(data: object) -> tuple[dict, list[str]]:
    errors = []

    if not isinstance(data, dict):
        return {"presets": [], "categories": []}, ["presets data must be an object"]

    presets = data.get("presets", [])
    categories = data.get("categories", [])

    if not isinstance(presets, list):
        return {"presets": [], "categories": []}, ["presets must be a list"]
    if not isinstance(categories, list):
        return {"presets": [], "categories": []}, ["categories must be a list"]

    valid_presets = []
    seen_ids = set()

    for index, preset in enumerate(presets):
        label = preset.get("id", f"#{index}") if isinstance(preset, dict) else f"#{index}"

        if not isinstance(preset, dict):
            errors.append(f"preset {label} is not an object")
            continue

        missing = [field for field in REQUIRED_PRESET_FIELDS if field not in preset]
        if missing:
            errors.append(f"preset {label} is missing fields: {', '.join(missing)}")
            continue

        if preset["id"] in seen_ids:
            errors.append(f"duplicate preset id: {preset['id']}")
            continue

        lights = preset.get("lights")
        if not isinstance(lights, list) or not lights or not all(_is_xy_color(color) for color in lights):
            errors.append(f"preset {label} has invalid lights")
            continue

        optional_errors = _validate_optional_fields(preset, label)
        if optional_errors:
            errors.extend(optional_errors)
            continue

        seen_ids.add(preset["id"])
        valid_presets.append(preset)

    valid_categories = [
        category
        for category in categories
        if isinstance(category, dict) and "id" in category and "name" in category
    ]
    if len(valid_categories) != len(categories):
        errors.append("some categories are invalid")

    return {"presets": valid_presets, "categories": valid_categories}, errors


def merge_presets(base: dict, custom: object) -> tuple[dict, list[str]]:
    merged = {
        "presets": list(base.get("presets", [])),
        "categories": list(base.get("categories", [])),
    }
    existing_preset_ids = {preset["id"] for preset in merged["presets"]}
    existing_category_ids = {category["id"] for category in merged["categories"]}

    valid_custom, errors = validate_presets(custom)

    for preset in valid_custom["presets"]:
        if preset["id"] in existing_preset_ids:
            errors.append(f"custom preset id conflicts with an existing preset: {preset['id']}")
            continue
        merged["presets"].append({**preset, "custom": True})
        existing_preset_ids.add(preset["id"])

    for category in valid_custom["categories"]:
        if category["id"] in existing_category_ids:
            errors.append(f"custom category id conflicts with an existing category: {category['id']}")
            continue
        merged["categories"].append({**category, "custom": True})
        existing_category_ids.add(category["id"])

    return merged, errors
