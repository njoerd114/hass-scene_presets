from __future__ import annotations

import re
import uuid

SAFE_FILENAME = re.compile(r"[^A-Za-z0-9._-]+")
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
MAX_IMAGE_BYTES = 5 * 1024 * 1024
DEFAULT_CATEGORY_NAME = "My Presets"


def new_preset_id() -> str:
    return str(uuid.uuid4())


def new_category_id() -> str:
    return str(uuid.uuid4())


def sanitize_filename(filename: str) -> str:
    name = SAFE_FILENAME.sub("-", filename).strip(".-") or "image"
    return name[:100]


def image_extension(filename: str) -> str:
    _, _, extension = filename.rpartition(".")
    return extension.lower()


def is_allowed_image(filename: str) -> bool:
    return image_extension(filename) in ALLOWED_IMAGE_EXTENSIONS


def find_category_id(data: dict, name: str) -> str | None:
    for category in data.get("categories", []):
        if category.get("name") == name:
            return category.get("id")
    return None


def ensure_category(data: dict, name: str, category_id: str | None = None) -> str:
    existing = find_category_id(data, name)
    if existing:
        return existing

    resolved_id = category_id or new_category_id()
    data.setdefault("categories", []).append({"id": resolved_id, "name": name})
    return resolved_id


def upsert_preset(data: dict, preset: dict) -> dict:
    presets = data.setdefault("presets", [])
    for index, existing in enumerate(presets):
        if existing.get("id") == preset.get("id"):
            presets[index] = preset
            return data

    presets.append(preset)
    return data


def remove_preset(data: dict, preset_id: str) -> bool:
    presets = data.get("presets", [])
    remaining = [preset for preset in presets if preset.get("id") != preset_id]
    if len(remaining) == len(presets):
        return False

    data["presets"] = remaining
    return True


def build_preset(
    name: str,
    colors: list[dict],
    category_id: str,
    preset_id: str | None = None,
    brightness: int = 255,
    image: str | None = None,
    effect: str | None = None,
    kelvin: int | None = None,
    white: int | None = None,
    distribution: str | None = None,
    transition_style: str | None = None,
) -> dict:
    preset = {
        "id": preset_id or new_preset_id(),
        "categoryId": category_id,
        "name": name,
        "bri": brightness,
        "lights": [{"x": float(color["x"]), "y": float(color["y"])} for color in colors],
    }

    if image:
        preset["img"] = image
    if effect:
        preset["effect"] = effect
    if kelvin is not None:
        preset["kelvin"] = kelvin
    if white is not None:
        preset["white"] = white
    if distribution:
        preset["distribution"] = distribution
    if transition_style:
        preset["transition_style"] = transition_style

    return preset
