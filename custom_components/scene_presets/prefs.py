from __future__ import annotations
DEFAULT_PREFS = {"favorites": [], "targets": {}, "tunables": {}}

_KEYS = ("favorites", "targets", "tunables")


def normalize_prefs(data: object) -> dict:
    if not isinstance(data, dict):
        return {"favorites": [], "targets": {}, "tunables": {}}

    favorites = data.get("favorites", [])
    targets = data.get("targets", {})
    tunables = data.get("tunables", {})

    return {
        "favorites": [item for item in favorites if isinstance(item, str)] if isinstance(favorites, list) else [],
        "targets": targets if isinstance(targets, dict) else {},
        "tunables": tunables if isinstance(tunables, dict) else {},
    }


def merge_prefs(current: object, updates: object) -> dict:
    result = normalize_prefs(current)
    updates = updates if isinstance(updates, dict) else {}

    for key in _KEYS:
        if key in updates:
            result[key] = updates[key]

    return normalize_prefs(result)
