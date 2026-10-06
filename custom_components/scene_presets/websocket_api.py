import base64
import binascii
import os

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.helpers.dispatcher import async_dispatcher_send

from .const import DOMAIN, SIGNAL_PRESETS_CHANGED
from .file_utils import (
    BASE_PATH,
    PRESET_DATA,
    ensure_userdata_dirs,
    read_custom_presets,
    reload_preset_data,
    write_custom_presets,
)
from .prefs import normalize_prefs
from .preset_authoring import (
    DEFAULT_CATEGORY_NAME,
    MAX_IMAGE_BYTES,
    ensure_category,
    is_allowed_image,
    new_preset_id,
    remove_preset,
    sanitize_filename,
    upsert_preset,
)
from .preset_generation import generate_effect_presets
from .validation import validate_single_preset


def _write_bytes(path, data):
    with open(path, "wb") as handle:
        handle.write(data)


def async_setup_websocket_api(hass) -> None:
    data = hass.data.setdefault(DOMAIN, {})
    if data.get("websocket_registered"):
        return
    data["websocket_registered"] = True

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/get_dynamic_scenes",
        }
    )
    def ws_get_dynamic_scenes(
            hass, connection, msg
    ) -> None:
        manager = hass.data.get(DOMAIN, {}).get("dynamic_scene_manager")
        if manager is None:
            connection.send_result(msg["id"], {"dynamic_scenes": []})
            return

        connection.send_result(msg["id"], manager.get_all_as_dict())


    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/get_prefs",
        }
    )
    def ws_get_prefs(hass, connection, msg) -> None:
        store = hass.data.get(DOMAIN, {}).get("prefs_store")
        connection.send_result(msg["id"], normalize_prefs(store.data if store else None))


    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/get_config",
        }
    )
    def ws_get_config(hass, connection, msg) -> None:
        entries = hass.config_entries.async_entries(DOMAIN)
        options = entries[0].options if entries else {}
        connection.send_result(
            msg["id"],
            {"enable_server_sync": options.get("enable_server_sync", True)},
        )


    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/set_prefs",
            vol.Optional("favorites"): vol.All(list, [str]),
            vol.Optional("targets"): dict,
            vol.Optional("tunables"): dict,
        }
    )
    @websocket_api.async_response
    async def ws_set_prefs(hass, connection, msg) -> None:
        store = hass.data.get(DOMAIN, {}).get("prefs_store")
        if store is None:
            connection.send_error(msg["id"], "not_ready", "Preferences store is not available")
            return

        updates = {
            key: msg[key]
            for key in ("favorites", "targets", "tunables")
            if key in msg
        }
        data = await store.async_update(updates)
        connection.send_result(msg["id"], data)


    websocket_api.async_register_command(hass, ws_get_dynamic_scenes)
    websocket_api.async_register_command(hass, ws_get_prefs)
    websocket_api.async_register_command(hass, ws_get_config)
    websocket_api.async_register_command(hass, ws_set_prefs)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/get_effect_presets",
            vol.Optional("entity_id"): vol.Any(str, [str]),
            vol.Optional("targets"): dict,
        }
    )
    def ws_get_effect_presets(hass, connection, msg) -> None:
        from .util import ensure_list, resolve_targets

        targets = msg.get("targets")
        if targets:
            entity_ids = resolve_targets(
                hass,
                ensure_list(targets.get("entity_id")),
                ensure_list(targets.get("device_id")),
                ensure_list(targets.get("area_id")),
                ensure_list(targets.get("floor_id")),
                ensure_list(targets.get("label_id")),
            )
        else:
            raw = msg.get("entity_id")
            entity_ids = [raw] if isinstance(raw, str) else (raw or [])

        effects = []
        for entity_id in entity_ids:
            state = hass.states.get(entity_id)
            if state:
                effects.extend(state.attributes.get("effect_list") or [])

        connection.send_result(msg["id"], generate_effect_presets(effects))

    websocket_api.async_register_command(hass, ws_get_effect_presets)

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/get_categories",
        }
    )
    def ws_get_categories(hass, connection, msg) -> None:
        connection.send_result(msg["id"], {"categories": PRESET_DATA.get("categories", [])})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/save_preset",
            vol.Required("preset"): dict,
            vol.Optional("category_name"): vol.Any(str, None),
        }
    )
    @websocket_api.async_response
    async def ws_save_preset(hass, connection, msg) -> None:
        preset = dict(msg["preset"])
        preset.setdefault("id", new_preset_id())

        data = await hass.async_add_executor_job(read_custom_presets) or {"presets": [], "categories": []}

        category_name = msg.get("category_name")
        if category_name:
            preset["categoryId"] = ensure_category(data, category_name)
        elif not preset.get("categoryId"):
            preset["categoryId"] = ensure_category(data, DEFAULT_CATEGORY_NAME)

        errors = validate_single_preset(preset)
        if errors:
            connection.send_result(msg["id"], {"success": False, "errors": errors})
            return

        upsert_preset(data, preset)
        await hass.async_add_executor_job(write_custom_presets, data)
        reload_preset_data(data)
        async_dispatcher_send(hass, SIGNAL_PRESETS_CHANGED)

        connection.send_result(msg["id"], {"success": True, "preset": preset, "errors": []})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/delete_preset",
            vol.Required("preset_id"): str,
        }
    )
    @websocket_api.async_response
    async def ws_delete_preset(hass, connection, msg) -> None:
        data = await hass.async_add_executor_job(read_custom_presets) or {"presets": [], "categories": []}
        removed = remove_preset(data, msg["preset_id"])

        if removed:
            await hass.async_add_executor_job(write_custom_presets, data)
            reload_preset_data(data)
            async_dispatcher_send(hass, SIGNAL_PRESETS_CHANGED)

        connection.send_result(msg["id"], {"success": removed})

    @websocket_api.websocket_command(
        {
            vol.Required("type"): "scene_presets/save_preset_image",
            vol.Required("filename"): str,
            vol.Required("content"): str,
        }
    )
    @websocket_api.async_response
    async def ws_save_preset_image(hass, connection, msg) -> None:
        filename = msg["filename"]
        if not is_allowed_image(filename):
            connection.send_error(msg["id"], "invalid_image", "Unsupported image type")
            return

        try:
            raw = base64.b64decode(msg["content"], validate=True)
        except (ValueError, binascii.Error):
            connection.send_error(msg["id"], "invalid_image", "Invalid image data")
            return

        if len(raw) > MAX_IMAGE_BYTES:
            connection.send_error(msg["id"], "too_large", "Image exceeds the maximum size")
            return

        safe_name = f"{new_preset_id()}-{sanitize_filename(filename)}"
        path = os.path.join(BASE_PATH, "userdata/custom/assets", safe_name)

        await hass.async_add_executor_job(ensure_userdata_dirs)
        await hass.async_add_executor_job(_write_bytes, path, raw)

        connection.send_result(msg["id"], {"filename": safe_name})

    websocket_api.async_register_command(hass, ws_get_categories)
    websocket_api.async_register_command(hass, ws_save_preset)
    websocket_api.async_register_command(hass, ws_delete_preset)
    websocket_api.async_register_command(hass, ws_save_preset_image)
