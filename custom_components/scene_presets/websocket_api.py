import voluptuous as vol
from homeassistant.components import websocket_api

from .const import DOMAIN
from .prefs import normalize_prefs
from .preset_generation import generate_effect_presets


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
