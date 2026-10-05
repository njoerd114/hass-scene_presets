from __future__ import annotations
import random
from typing import Any


def pick_random_preset(presets: list[dict], category_id: str | None = None, rng: Any = None) -> dict | None:
    candidates = [
        preset
        for preset in presets
        if category_id is None or preset.get("categoryId") == category_id
    ]

    if not candidates:
        return None

    return (rng or random).choice(candidates)
