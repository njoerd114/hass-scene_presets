from __future__ import annotations
import base64
import binascii
import json

from .validation import validate_presets


def export_custom_presets(presets: list[dict], categories: list[dict] | None = None) -> str:
    custom_presets = [preset for preset in presets if preset.get("custom")]
    used_category_ids = {preset.get("categoryId") for preset in custom_presets}
    custom_categories = [
        category
        for category in (categories or [])
        if category.get("custom") or category.get("id") in used_category_ids
    ]

    return json.dumps(
        {"presets": custom_presets, "categories": custom_categories},
        indent=2,
        sort_keys=True,
    )


def encode_share(payload: str) -> str:
    return base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii")


def decode_share(code: str) -> str:
    return base64.urlsafe_b64decode(code.encode("ascii")).decode("utf-8")


def parse_import(payload: object) -> tuple[dict, list[str]]:
    empty = {"presets": [], "categories": []}

    if not isinstance(payload, str):
        return validate_presets(payload)

    text = payload.strip()
    if not text:
        return empty, ["payload is empty"]

    if not text.startswith("{"):
        try:
            text = decode_share(text)
        except (ValueError, UnicodeDecodeError, binascii.Error):
            return empty, ["payload is neither JSON nor a valid share code"]

    try:
        data = json.loads(text)
    except json.JSONDecodeError as err:
        return empty, [f"invalid JSON: {err}"]

    return validate_presets(data)
