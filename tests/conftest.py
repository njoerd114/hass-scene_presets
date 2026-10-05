import importlib.util
import math
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG_DIR = ROOT / "custom_components" / "scene_presets"


def _install_voluptuous_stub():
    try:
        import voluptuous  # noqa: F401
        return
    except ImportError:
        pass

    vol = types.ModuleType("voluptuous")

    class Invalid(Exception):
        pass

    vol.Invalid = Invalid
    sys.modules["voluptuous"] = vol


def _install_homeassistant_stub():
    if "homeassistant.util.color" in sys.modules:
        return

    color = types.ModuleType("homeassistant.util.color")

    def _clamp(value):
        return max(0.0, min(255.0, value))

    def color_temperature_to_rgb(kelvin):
        t = max(1000.0, min(40000.0, float(kelvin))) / 100.0
        if t <= 66:
            r = 255.0
            g = 99.4708025861 * math.log(t) - 161.1195681661
        else:
            r = 329.698727446 * ((t - 60.0) ** -0.1332047592)
            g = 288.1221695283 * ((t - 60.0) ** -0.0755148492)
        if t >= 66:
            b = 255.0
        elif t <= 19:
            b = 0.0
        else:
            b = 138.5177312231 * math.log(t - 10.0) - 305.0447927307
        return (_clamp(r), _clamp(g), _clamp(b))

    def color_RGB_to_xy(r, g, b):
        total = r + g + b
        if total <= 0:
            return (0.0, 0.0)
        return (r / total, g / total)

    color.color_temperature_to_rgb = color_temperature_to_rgb
    color.color_RGB_to_xy = color_RGB_to_xy

    def color_xy_to_RGB(x, y, brightness=255):
        total = x + y
        if total <= 0:
            return (0.0, 0.0, 0.0)
        return (brightness * x / total, brightness * y / total, 0.0)

    def color_RGB_to_hs(r, g, b):
        return (0.0, 0.0)

    color.color_xy_to_RGB = color_xy_to_RGB
    color.color_RGB_to_hs = color_RGB_to_hs

    util = types.ModuleType("homeassistant.util")
    util.color = color

    helpers = types.ModuleType("homeassistant.helpers")
    helpers.entity_registry = types.ModuleType("homeassistant.helpers.entity_registry")
    helpers.device_registry = types.ModuleType("homeassistant.helpers.device_registry")
    helpers.area_registry = types.ModuleType("homeassistant.helpers.area_registry")

    homeassistant = types.ModuleType("homeassistant")
    homeassistant.util = util
    homeassistant.helpers = helpers

    sys.modules["homeassistant"] = homeassistant
    sys.modules["homeassistant.util"] = util
    sys.modules["homeassistant.util.color"] = color
    sys.modules["homeassistant.helpers"] = helpers
    sys.modules["homeassistant.helpers.entity_registry"] = helpers.entity_registry
    sys.modules["homeassistant.helpers.device_registry"] = helpers.device_registry
    sys.modules["homeassistant.helpers.area_registry"] = helpers.area_registry


def _expose_scene_presets_package():
    if "scene_presets" in sys.modules:
        return

    spec = importlib.util.spec_from_file_location(
        "scene_presets",
        PKG_DIR / "__init__.py",
        submodule_search_locations=[str(PKG_DIR)],
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules["scene_presets"] = module


_install_voluptuous_stub()
_install_homeassistant_stub()
_expose_scene_presets_package()
