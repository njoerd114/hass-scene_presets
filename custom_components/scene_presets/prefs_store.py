from __future__ import annotations
from .prefs import DEFAULT_PREFS, merge_prefs, normalize_prefs

STORAGE_VERSION = 1
STORAGE_KEY = "scene_presets.prefs"
SAVE_DELAY = 1


class PrefsStore:
    def __init__(self, hass=None, store=None):
        if store is None:
            from homeassistant.helpers.storage import Store

            store = Store(hass, STORAGE_VERSION, STORAGE_KEY)

        self._store = store
        self.data = dict(DEFAULT_PREFS)

    async def async_load(self):
        stored = await self._store.async_load()
        self.data = normalize_prefs(stored)
        return self.data

    async def async_update(self, updates):
        self.data = merge_prefs(self.data, updates)
        self._store.async_delay_save(lambda: self.data, SAVE_DELAY)
        return self.data
