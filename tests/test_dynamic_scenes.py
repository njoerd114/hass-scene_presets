import asyncio
from contextlib import suppress

from scene_presets import dynamic_scenes as ds


class FakeState:
    def __init__(self, attributes, state="on"):
        self.attributes = attributes
        self.state = state


class FakeStates:
    def __init__(self, mapping):
        self._mapping = mapping

    def get(self, entity_id):
        return self._mapping.get(entity_id)


class FakeServices:
    def __init__(self):
        self.calls = []

    async def async_call(self, domain, service, data, blocking=False):
        self.calls.append({"domain": domain, "service": service, "data": data})


class FakeHass:
    def __init__(self, states):
        self.states = FakeStates(states)
        self.services = FakeServices()

    def create_task(self, coro):
        return asyncio.get_running_loop().create_task(coro)


def test_dynamic_scene_survives_apply_failures(monkeypatch):
    async def scenario():
        call_count = {"n": 0}

        async def failing_apply(*args, **kwargs):
            call_count["n"] += 1
            raise RuntimeError("boom")

        monkeypatch.setattr(ds, "apply_preset", failing_apply)

        hass = FakeHass({"light.a": FakeState({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]}, "on")})
        parameters = {
            "preset_id": "p",
            "light_entity_ids": ["light.a"],
            "transition": 1,
            "shuffle": True,
            "brightness": None,
            "effect": None,
        }

        scene = ds.DynamicScene(hass, lambda scene_id: None, parameters, 0.01)
        await asyncio.sleep(0.06)

        task = scene._task
        assert call_count["n"] >= 2
        assert task is not None and not task.done()

        scene.stop_loop()
        with suppress(asyncio.CancelledError):
            await task

    asyncio.run(scenario())


def test_dynamic_scene_stops_when_all_lights_turn_off(monkeypatch):
    async def scenario():
        destroyed = []

        async def noop_apply(*args, **kwargs):
            return None

        monkeypatch.setattr(ds, "apply_preset", noop_apply)

        hass = FakeHass({"light.a": FakeState({"supported_color_modes": ["xy"]}, "off")})
        parameters = {
            "preset_id": "p",
            "light_entity_ids": ["light.a"],
            "transition": 1,
            "shuffle": True,
            "brightness": None,
            "effect": None,
        }

        scene = ds.DynamicScene(hass, lambda scene_id: destroyed.append(scene_id), parameters, 0.01)
        await asyncio.sleep(0.06)

        assert destroyed == [scene.id]

    asyncio.run(scenario())


def test_dynamic_scene_handles_missing_entity_state(monkeypatch):
    async def scenario():
        destroyed = []

        async def noop_apply(*args, **kwargs):
            return None

        monkeypatch.setattr(ds, "apply_preset", noop_apply)

        hass = FakeHass({})
        parameters = {
            "preset_id": "p",
            "light_entity_ids": ["light.gone"],
            "transition": 1,
            "shuffle": True,
            "brightness": None,
            "effect": None,
        }

        scene = ds.DynamicScene(hass, lambda scene_id: destroyed.append(scene_id), parameters, 0.01)
        await asyncio.sleep(0.06)

        assert destroyed == [scene.id]

    asyncio.run(scenario())
