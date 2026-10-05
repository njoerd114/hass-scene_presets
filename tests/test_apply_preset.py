import asyncio
import sys
import types

from scene_presets import presets as presets_mod

PRESET = {"id": "test", "bri": 100, "lights": [{"x": 0.4, "y": 0.4}]}


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


def _light(attributes, state="on"):
    return FakeState(attributes, state)


def _preset_data(monkeypatch, *presets):
    monkeypatch.setattr(presets_mod, "PRESET_DATA", {"presets": list(presets)})


def test_preset_defined_effect_is_applied(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "effect": "Rainbow"})
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "effect_list": ["Rainbow"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls[0]["data"]["effect"] == "Rainbow"
    assert hass.services.calls[0]["data"]["xy_color"] == (0.4, 0.4)


def test_effect_override_wins_over_preset_effect(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "effect": "Rainbow"})
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "effect_list": ["Rainbow", "Meteor"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False, effect_override="Meteor"))

    assert hass.services.calls[0]["data"]["effect"] == "Meteor"


def test_effect_is_ignored_by_lights_without_effects(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "effect": "Rainbow"})
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert "effect" not in hass.services.calls[0]["data"]


def test_unknown_effect_is_not_sent_to_the_light(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "effect": "Rainbow"})
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "effect_list": ["Meteor"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert "effect" not in hass.services.calls[0]["data"]


def test_brightness_override_of_zero_is_honoured(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False, brightness_override=0))

    assert hass.services.calls[0]["data"]["brightness"] == 0


def test_missing_brightness_override_uses_preset_brightness(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls[0]["data"]["brightness"] == 100


def test_color_temperature_light_gets_kelvin(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["color_temp"]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert isinstance(hass.services.calls[0]["data"]["color_temp_kelvin"], int)


def test_onoff_only_light_is_skipped(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["onoff"]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls == []


def test_none_color_modes_does_not_crash(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": None, "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls == []


def test_missing_color_modes_is_skipped(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls == []


def test_rgbww_light_gets_rgb_color(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["rgbww"]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert "rgb_color" in hass.services.calls[0]["data"]


def test_preset_white_channel_is_used_for_rgbw(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "white": 200})
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["rgbw"]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls[0]["data"]["rgbw_color"][3] == 200


def test_easing_transition_style_issues_stepped_calls(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3], "brightness": 10})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 2, False, False, transition_style_override="ease_in_out"))

    assert len(hass.services.calls) == 5
    assert all(call["data"]["brightness"] >= 1 for call in hass.services.calls)


def test_easing_preserves_zero_brightness_override(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3], "brightness": 50})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 2, False, False, brightness_override=0, transition_style_override="ease_in_out"))

    assert hass.services.calls[-1]["data"]["brightness"] == 0


def test_white_only_light_applies_brightness_without_color(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["white"]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    data = hass.services.calls[0]["data"]
    assert data["brightness"] == 100
    assert "xy_color" not in data
    assert "color_temp_kelvin" not in data


def _install_fake_wled(monkeypatch, sink, controls_sink=None):
    module = types.ModuleType("scene_presets.wled")

    async def fake_apply_wled_preset(hass, light_entity_ids, preset_name):
        sink.append((list(light_entity_ids), preset_name))

    async def fake_apply_wled_controls(hass, light_entity_ids, palette=None, speed=None, intensity=None):
        if controls_sink is not None:
            controls_sink.append((list(light_entity_ids), palette, speed, intensity))

    module.apply_wled_preset = fake_apply_wled_preset
    module.apply_wled_controls = fake_apply_wled_controls
    monkeypatch.setitem(sys.modules, "scene_presets.wled", module)
    return module


def test_preset_wled_preset_triggers_select(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "wled_preset": "My Preset"})
    sink = []
    _install_fake_wled(monkeypatch, sink)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert sink == [(["light.a"], "My Preset")]


def test_wled_preset_override_wins(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "wled_preset": "My Preset"})
    sink = []
    _install_fake_wled(monkeypatch, sink)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False, wled_preset_override="Other"))

    assert sink == [(["light.a"], "Other")]


def test_no_wled_preset_leaves_wled_untouched(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    sink = []
    _install_fake_wled(monkeypatch, sink)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert sink == []


def test_apply_preset_does_not_mutate_target_list(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    ids = ["light.a", "light.b", "light.c"]
    original = list(ids)
    hass = FakeHass({entity_id: _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]}) for entity_id in ids})

    asyncio.run(presets_mod.apply_preset(hass, "test", ids, 1, True, True))

    assert ids == original


def test_preset_kelvin_is_used_for_color_temp_lights(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "kelvin": 2200})
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["color_temp"]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert hass.services.calls[0]["data"]["color_temp_kelvin"] == 2200


def test_wled_controls_are_applied(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "wled_palette": "Rainbow", "wled_speed": 128, "wled_intensity": 64})
    sink = []
    controls = []
    _install_fake_wled(monkeypatch, sink, controls)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert controls == [(["light.a"], "Rainbow", 128, 64)]


def test_wled_control_overrides_win(monkeypatch):
    _preset_data(monkeypatch, {**PRESET, "wled_palette": "Rainbow", "wled_speed": 128})
    sink = []
    controls = []
    _install_fake_wled(monkeypatch, sink, controls)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False, wled_palette_override="Fire", wled_speed_override=200))

    assert controls == [(["light.a"], "Fire", 200, None)]


def test_no_wled_controls_leaves_controls_untouched(monkeypatch):
    _preset_data(monkeypatch, PRESET)
    sink = []
    controls = []
    _install_fake_wled(monkeypatch, sink, controls)
    hass = FakeHass({"light.a": _light({"supported_color_modes": ["xy"], "xy_color": [0.3, 0.3]})})

    asyncio.run(presets_mod.apply_preset(hass, "test", ["light.a"], 1, False, False))

    assert controls == []
