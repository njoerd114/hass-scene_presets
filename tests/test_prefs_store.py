import asyncio

from scene_presets.prefs_store import PrefsStore


class FakeHAStore:
    def __init__(self, initial=None):
        self.initial = initial
        self.saved = None

    async def async_load(self):
        return self.initial

    def async_delay_save(self, callback, delay):
        self.saved = callback()


def test_load_normalizes_stored_data():
    prefs = PrefsStore(store=FakeHAStore(initial={"favorites": ["a", 1]}))

    data = asyncio.run(prefs.async_load())

    assert data["favorites"] == ["a"]


def test_update_merges_and_saves():
    ha_store = FakeHAStore(initial=None)
    prefs = PrefsStore(store=ha_store)
    asyncio.run(prefs.async_load())

    data = asyncio.run(prefs.async_update({"favorites": ["b"]}))

    assert data["favorites"] == ["b"]
    assert ha_store.saved["favorites"] == ["b"]


def test_update_without_load_uses_defaults():
    prefs = PrefsStore(store=FakeHAStore())

    data = asyncio.run(prefs.async_update({"targets": {"entity_id": "light.x"}}))

    assert data["targets"] == {"entity_id": "light.x"}
    assert data["favorites"] == []


def test_update_ignores_unknown_keys():
    prefs = PrefsStore(store=FakeHAStore())
    asyncio.run(prefs.async_load())

    data = asyncio.run(prefs.async_update({"nope": 1, "favorites": ["a"]}))

    assert data["favorites"] == ["a"]
    assert "nope" not in data
