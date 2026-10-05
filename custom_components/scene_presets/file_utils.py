import json
import os
import logging

from .validation import merge_presets, validate_presets

_LOGGER = logging.getLogger(__name__)

BASE_PATH = os.path.dirname(os.path.realpath(__file__))


def _read_json(path, required):
    try:
        with open(path, "r", encoding="utf-8") as file:
            return json.load(file)
    except FileNotFoundError:
        if required:
            raise RuntimeError(f"Required file '{path}' is missing.")
        _LOGGER.info("No custom presets file found at %s", path)
        return None
    except (json.JSONDecodeError, OSError) as err:
        if required:
            raise RuntimeError(f"Failed to load required file '{path}': {err}") from err
        _LOGGER.error("Error loading custom presets from '%s': %s", path, err)
        return None


MANIFEST = _read_json(os.path.join(BASE_PATH, 'manifest.json'), required=True)
VERSION = MANIFEST['version']

USERDATA_ASSETS_PATH = os.path.join(BASE_PATH, 'userdata/custom/assets')


def ensure_userdata_dirs():
    os.makedirs(USERDATA_ASSETS_PATH, exist_ok=True)
    return USERDATA_ASSETS_PATH


_raw_preset_data = _read_json(os.path.join(BASE_PATH, 'presets.json'), required=True)
_BUILTIN_PRESET_DATA, _builtin_errors = validate_presets(_raw_preset_data)
for _error in _builtin_errors:
    _LOGGER.error("Invalid built-in preset data: %s", _error)

CUSTOM_PRESETS = _read_json(os.path.join(BASE_PATH, 'userdata/custom/presets.json'), required=False)

PRESET_DATA, _custom_errors = merge_presets(
    _BUILTIN_PRESET_DATA,
    CUSTOM_PRESETS or {"presets": [], "categories": []},
)
for _error in _custom_errors:
    _LOGGER.error("Invalid custom preset data: %s", _error)


CUSTOM_PRESETS_PATH = os.path.join(BASE_PATH, 'userdata/custom/presets.json')


def read_custom_presets():
    return _read_json(CUSTOM_PRESETS_PATH, required=False)


def write_custom_presets(data):
    ensure_userdata_dirs()
    with open(CUSTOM_PRESETS_PATH, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, sort_keys=True)
    return CUSTOM_PRESETS_PATH


def reload_preset_data(custom_data=None):
    if custom_data is None:
        custom_data = read_custom_presets()

    merged, errors = merge_presets(
        _BUILTIN_PRESET_DATA,
        custom_data or {"presets": [], "categories": []},
    )

    PRESET_DATA.clear()
    PRESET_DATA.update(merged)

    return errors
