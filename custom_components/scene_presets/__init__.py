import voluptuous as vol
import homeassistant.helpers.config_validation as cv
import asyncio
import logging
from datetime import timedelta
from homeassistant.core import HomeAssistant, SupportsResponse
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from .const import *

from .dynamic_scenes import DynamicScene, DynamicSceneManager
from .presets import apply_preset
from .file_utils import PRESET_DATA, read_custom_presets, write_custom_presets, ensure_userdata_dirs, reload_preset_data
from .selection import pick_random_preset
from .prefs_store import PrefsStore
from .portability import encode_share, export_custom_presets, parse_import
from .preset_generation import generate_effect_presets
from .validation import merge_presets
from .scheduler import SceneScheduler
from .preset_watcher import PresetWatcher
from .schedule import due_entries, fired_key
from .view import async_setup_view, async_remove_view
from .util import ensure_list, resolve_targets
from .websocket_api import async_setup_websocket_api

CONFIG_SCHEMA = cv.empty_config_schema(DOMAIN)

SCHEDULE_STORE_VERSION = 1
SCHEDULE_STORE_KEY = "scene_presets.schedule"

APPLY_PRESET_SCHEMA = vol.Schema({
    vol.Required(ATTR_SCENE_PRESET_ID): cv.string,
    vol.Required(ATTR_TARGETS): vol.Any(dict),
    vol.Optional(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_TRANSITION, default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
    vol.Optional(ATTR_SHUFFLE, default=False): cv.boolean,
    vol.Optional(ATTR_SMART_SHUFFLE, default=False): cv.boolean,
    vol.Optional(ATTR_EFFECT): cv.string,
    vol.Optional(ATTR_WLED_PRESET): cv.string,
    vol.Optional(ATTR_WLED_PALETTE): cv.string,
    vol.Optional(ATTR_WLED_SPEED): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_WLED_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional("distribution"): vol.In(["sequence", "balanced", "random"]),
    vol.Optional("transition_style"): vol.In(["fade", "instant", "ease_in", "ease_out", "ease_in_out"])
})

APPLY_RANDOM_PRESET_SCHEMA = vol.Schema({
    vol.Required(ATTR_TARGETS): vol.Any(dict),
    vol.Optional(ATTR_CATEGORY_ID): cv.string,
    vol.Optional(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_TRANSITION, default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
    vol.Optional(ATTR_SHUFFLE, default=False): cv.boolean,
    vol.Optional(ATTR_SMART_SHUFFLE, default=False): cv.boolean,
    vol.Optional("distribution"): vol.In(["sequence", "balanced", "random"]),
    vol.Optional("transition_style"): vol.In(["fade", "instant", "ease_in", "ease_out", "ease_in_out"])
})

START_DYNAMIC_SCENE_SCHEMA = vol.Schema({
    vol.Required(ATTR_SCENE_PRESET_ID): cv.string,
    vol.Required(ATTR_TARGETS): vol.Any(dict),
    vol.Optional(ATTR_INTERVAL, default=60): vol.All(vol.Coerce(int), vol.Range(min=1, max=86400)),
    vol.Optional(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_TRANSITION, default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
    vol.Optional(ATTR_EFFECT): cv.string,
    vol.Optional(ATTR_WLED_PRESET): cv.string,
    vol.Optional(ATTR_WLED_PALETTE): cv.string,
    vol.Optional(ATTR_WLED_SPEED): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_WLED_INTENSITY): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional("distribution"): vol.In(["sequence", "balanced", "random"]),
    vol.Optional("transition_style"): vol.In(["fade", "instant", "ease_in", "ease_out", "ease_in_out"])
})

STOP_DYNAMIC_SCENE_SCHEMA = vol.Schema({
    vol.Required(ATTR_DYNAMIC_SCENE_ID): cv.string,
})

STOP_DYNAMIC_SCENES_FOR_TARGETS_SCHEMA = vol.Schema({
    vol.Required(ATTR_TARGETS): vol.Any(dict),
})

IMPORT_PRESETS_SCHEMA = vol.Schema({
    vol.Required(ATTR_PAYLOAD): cv.string,
})

GENERATE_EFFECT_PRESETS_SCHEMA = vol.Schema({
    vol.Required(ATTR_ENTITY_ID): vol.Any(cv.string, [cv.string]),
})

START_CIRCADIAN_SCHEMA = vol.Schema({
    vol.Required(ATTR_TARGETS): vol.Any(dict),
    vol.Optional("min_kelvin", default=3000): vol.All(vol.Coerce(int), vol.Range(min=1000, max=10000)),
    vol.Optional("max_kelvin", default=6500): vol.All(vol.Coerce(int), vol.Range(min=1000, max=10000)),
    vol.Optional("sleep_kelvin", default=1900): vol.All(vol.Coerce(int), vol.Range(min=1000, max=10000)),
    vol.Optional("min_brightness", default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    vol.Optional("max_brightness", default=100): vol.All(vol.Coerce(int), vol.Range(min=0, max=100)),
    vol.Optional("interval", default=60): vol.All(vol.Coerce(int), vol.Range(min=5, max=86400)),
})

SET_SCHEDULE_SCHEMA = vol.Schema({
    vol.Required("schedule"): [vol.Any(dict)],
})

APPLY_EFFECT_SCHEMA = vol.Schema({
    vol.Required(ATTR_TARGETS): vol.Any(dict),
    vol.Required(ATTR_EFFECT): cv.string,
    vol.Optional(ATTR_BRIGHTNESS): vol.All(vol.Coerce(int), vol.Range(min=0, max=255)),
    vol.Optional(ATTR_TRANSITION, default=1): vol.All(vol.Coerce(int), vol.Range(min=0, max=300)),
})


_LOGGER = logging.getLogger(__name__)


def _get_manager(hass):
    data = hass.data.setdefault(DOMAIN, {})
    manager = data.get("dynamic_scene_manager")
    if manager is None:
        manager = DynamicSceneManager()
        data["dynamic_scene_manager"] = manager
    return manager


def _get_scheduler(hass):
    data = hass.data.setdefault(DOMAIN, {})
    scheduler = data.get("circadian_scheduler")
    if scheduler is None:
        scheduler = SceneScheduler(hass)
        data["circadian_scheduler"] = scheduler
    return scheduler


def _stop_background(hass):
    data = hass.data.get(DOMAIN, {})

    manager = data.get("dynamic_scene_manager")
    if manager is not None:
        manager.stop_all()

    scheduler = data.get("circadian_scheduler")
    if scheduler is not None:
        scheduler.stop()

    cancel_watch = data.get("preset_watch_cancel")
    if cancel_watch is not None:
        cancel_watch()

    cancel_schedule = data.get("schedule_cancel")
    if cancel_schedule is not None:
        cancel_schedule()


async def _run_schedule_entry(hass, entry):
    preset_id = entry.get("preset_id")
    if not preset_id:
        return

    targets = entry.get("targets") or {}
    entity_ids = ensure_list(targets.get("entity_id"))
    device_ids = ensure_list(targets.get("device_id"))
    area_ids = ensure_list(targets.get("area_id"))
    floor_ids = ensure_list(targets.get("floor_id"))
    label_ids = ensure_list(targets.get("label_id"))

    light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

    if not light_entity_ids:
        _LOGGER.warning("Scheduled preset '%s' had no matching light entities", preset_id)
        return

    _LOGGER.debug("Applying scheduled preset '%s' to %s", preset_id, light_entity_ids)

    await apply_preset(
        hass,
        preset_id,
        light_entity_ids,
        entry.get("transition", 1),
        entry.get("shuffle", False),
        entry.get("smart_shuffle", False),
        entry.get("brightness"),
        entry.get("effect"),
        entry.get("wled_preset"),
        entry.get("wled_palette"),
        entry.get("wled_speed"),
        entry.get("wled_intensity"),
        entry.get("distribution"),
        entry.get("transition_style"),
    )


async def async_setup(hass, config):
    async def apply_preset_service(call):
        preset_id = call.data.get(ATTR_SCENE_PRESET_ID)
        targets = call.data.get(ATTR_TARGETS)
        brightness_override = call.data.get(ATTR_BRIGHTNESS)
        transition = call.data.get(ATTR_TRANSITION, 1)
        shuffle = call.data.get(ATTR_SHUFFLE, False)
        smart_shuffle = call.data.get(ATTR_SMART_SHUFFLE, False)
        effect_override = call.data.get(ATTR_EFFECT)
        wled_preset_override = call.data.get(ATTR_WLED_PRESET)
        wled_palette_override = call.data.get(ATTR_WLED_PALETTE)
        wled_speed_override = call.data.get(ATTR_WLED_SPEED)
        wled_intensity_override = call.data.get(ATTR_WLED_INTENSITY)
        distribution_override = call.data.get("distribution")
        transition_style_override = call.data.get("transition_style")

        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))


        light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

        if not light_entity_ids:
            _LOGGER.warning(
                "Preset '%s' was not applied because no light entities matched the given targets",
                preset_id,
            )
            return

        _LOGGER.debug("Applying preset '%s' to %s", preset_id, light_entity_ids)

        await apply_preset(
            hass,
            preset_id,
            light_entity_ids,
            transition,
            shuffle,
            smart_shuffle,
            brightness_override,
            effect_override,
            wled_preset_override,
            wled_palette_override,
            wled_speed_override,
            wled_intensity_override,
            distribution_override,
            transition_style_override
        )


    async def apply_random_preset_service(call):
        targets = call.data.get(ATTR_TARGETS)
        category_id = call.data.get(ATTR_CATEGORY_ID)
        brightness_override = call.data.get(ATTR_BRIGHTNESS)
        transition = call.data.get(ATTR_TRANSITION, 1)
        shuffle = call.data.get(ATTR_SHUFFLE, False)
        smart_shuffle = call.data.get(ATTR_SMART_SHUFFLE, False)

        preset = pick_random_preset(PRESET_DATA.get("presets", []), category_id)
        if preset is None:
            _LOGGER.warning("No preset found for category '%s'", category_id)
            return

        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))

        light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

        if not light_entity_ids:
            _LOGGER.warning(
                "Random preset '%s' was not applied because no light entities matched the given targets",
                preset["id"],
            )
            return

        _LOGGER.debug("Applying random preset '%s' to %s", preset["id"], light_entity_ids)

        await apply_preset(
            hass,
            preset["id"],
            light_entity_ids,
            transition,
            shuffle,
            smart_shuffle,
            brightness_override,
            None,
            None,
            None,
            None,
            None,
            call.data.get("distribution"),
            call.data.get("transition_style")
        )

    async def apply_effect_service(call):
        targets = call.data.get(ATTR_TARGETS)
        effect = call.data.get(ATTR_EFFECT)
        brightness = call.data.get(ATTR_BRIGHTNESS)
        transition = call.data.get(ATTR_TRANSITION, 1)

        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))

        light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

        if not light_entity_ids:
            _LOGGER.warning("Effect '%s' was not applied because no light entities matched", effect)
            return

        tasks = []
        for entity_id in light_entity_ids:
            state = hass.states.get(entity_id)
            if state is None or effect not in (state.attributes.get("effect_list") or []):
                continue
            params = {"entity_id": entity_id, "effect": effect, "transition": transition}
            if brightness is not None:
                params["brightness"] = brightness
            tasks.append(hass.services.async_call("light", "turn_on", params, blocking=False))

        if tasks:
            await asyncio.gather(*tasks)

    async def start_dynamic_scene(call):
        # always stop any existing actions first
        stopped = await stop_dynamic_scenes_for_targets(call)

        preset_id = call.data.get(ATTR_SCENE_PRESET_ID)
        targets = call.data.get(ATTR_TARGETS)
        interval = call.data.get(ATTR_INTERVAL)

        brightness_override = call.data.get(ATTR_BRIGHTNESS)
        transition = call.data.get(ATTR_TRANSITION, 1)
        shuffle = True
        effect_override = call.data.get(ATTR_EFFECT)
        wled_preset_override = call.data.get(ATTR_WLED_PRESET)
        wled_palette_override = call.data.get(ATTR_WLED_PALETTE)
        wled_speed_override = call.data.get(ATTR_WLED_SPEED)
        wled_intensity_override = call.data.get(ATTR_WLED_INTENSITY)
        distribution_override = call.data.get("distribution")
        transition_style_override = call.data.get("transition_style")

        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))

        light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

        if not light_entity_ids:
            _LOGGER.warning(
                "Dynamic scene for preset '%s' was not started because no light entities matched the given targets",
                preset_id,
            )
            return None

        _LOGGER.debug("Starting dynamic scene for preset '%s' on %s", preset_id, light_entity_ids)

        scene = _get_manager(hass).create_new(
            hass,
            {
                "preset_id": preset_id,
                "light_entity_ids": light_entity_ids,
                "brightness": brightness_override,
                "transition": transition,
                "shuffle": shuffle,
                "effect": effect_override,
                "wled_preset": wled_preset_override,
                "wled_palette": wled_palette_override,
                "wled_speed": wled_speed_override,
                "wled_intensity": wled_intensity_override,
                "distribution": distribution_override,
                "transition_style": transition_style_override
            },
            interval
        )

        return {"dynamic_scene": scene, "stopped": stopped}

    async def stop_dynamic_scene(call):
        scene_id = call.data.get(ATTR_DYNAMIC_SCENE_ID)

        _LOGGER.debug("Stopping dynamic scene %s", scene_id)

        _get_manager(hass).delete_by_id(scene_id)

    async def stop_dynamic_scenes_for_targets(call):
        targets = call.data.get(ATTR_TARGETS)

        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))

        light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

        stopped = 0
        for light_entity_id in light_entity_ids:
            before = len(_get_manager(hass).dynamic_scenes)
            _get_manager(hass).stop_all_for_entity_id(light_entity_id)
            stopped += before - len(_get_manager(hass).dynamic_scenes)

        return stopped

    async def stop_all_dynamic_scenes(call):
        _LOGGER.debug("Stopping all dynamic scenes")
        _get_manager(hass).stop_all()

    async def get_dynamic_scenes(call):
        return _get_manager(hass).get_all_as_dict()

    async def export_presets_service(call):
        payload = export_custom_presets(
            PRESET_DATA.get("presets", []),
            PRESET_DATA.get("categories", []),
        )
        return {"payload": payload, "share": encode_share(payload)}

    async def import_presets_service(call):
        valid, errors = parse_import(call.data.get(ATTR_PAYLOAD))
        if not valid["presets"] and not valid["categories"]:
            return {"imported": 0, "errors": errors}

        existing = await hass.async_add_executor_job(read_custom_presets) or {"presets": [], "categories": []}
        merged, merge_errors = merge_presets(
            existing,
            {"presets": valid["presets"], "categories": valid["categories"]},
        )
        await hass.async_add_executor_job(
            write_custom_presets,
            {"presets": merged["presets"], "categories": merged["categories"]},
        )

        reload_preset_data(merged)
        async_dispatcher_send(hass, SIGNAL_PRESETS_CHANGED)

        return {"imported": len(valid["presets"]), "errors": errors + merge_errors}

    async def generate_effect_presets_service(call):
        entity_ids = ensure_list(call.data.get(ATTR_ENTITY_ID))
        effects = []
        for entity_id in entity_ids:
            state = hass.states.get(entity_id)
            if state:
                effects.extend(state.attributes.get("effect_list") or [])

        if not effects:
            return {"imported": 0, "errors": ["No effects found on the given entities"]}

        generated = generate_effect_presets(effects)
        existing = await hass.async_add_executor_job(read_custom_presets) or {"presets": [], "categories": []}
        merged, merge_errors = merge_presets(
            existing,
            {"presets": generated["presets"], "categories": [generated["category"]]},
        )
        await hass.async_add_executor_job(
            write_custom_presets,
            {"presets": merged["presets"], "categories": merged["categories"]},
        )

        reload_preset_data(merged)
        async_dispatcher_send(hass, SIGNAL_PRESETS_CHANGED)

        return {"imported": len(generated["presets"]), "errors": merge_errors}


    async def start_circadian(call):
        targets = call.data.get(ATTR_TARGETS)

        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))

        light_entity_ids = resolve_targets(hass, entity_ids, device_ids, area_ids, floor_ids, label_ids)

        if not light_entity_ids:
            _LOGGER.warning(
                "Circadian lighting was not started because no light entities matched the given targets"
            )
            return

        _get_scheduler(hass).start(
            {
                "light_entity_ids": light_entity_ids,
                "min_kelvin": call.data.get("min_kelvin", 3000),
                "max_kelvin": call.data.get("max_kelvin", 6500),
                "sleep_kelvin": call.data.get("sleep_kelvin", 1900),
                "min_brightness": call.data.get("min_brightness", 1),
                "max_brightness": call.data.get("max_brightness", 100),
                "interval": call.data.get("interval", 60),
            }
        )
        _LOGGER.debug("Started circadian lighting for %s", light_entity_ids)

    async def stop_circadian(call):
        _LOGGER.debug("Stopping circadian lighting")
        _get_scheduler(hass).stop()

    async def set_schedule(call):
        schedules = call.data.get("schedule", [])
        hass.data.setdefault(DOMAIN, {})["schedules"] = schedules
        store = hass.data[DOMAIN].get("schedule_store")
        if store is not None:
            await store.async_save({"schedules": schedules})
        _LOGGER.debug("Saved %d scheduled presets", len(schedules))
        return {"schedules": schedules}

    async def clear_schedule(call):
        hass.data.setdefault(DOMAIN, {})["schedules"] = []
        store = hass.data[DOMAIN].get("schedule_store")
        if store is not None:
            await store.async_save({"schedules": []})

    async def get_schedule(call):
        return {"schedules": hass.data.get(DOMAIN, {}).get("schedules", [])}

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_PRESET,
        apply_preset_service,
        schema=APPLY_PRESET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_RANDOM_PRESET,
        apply_random_preset_service,
        schema=APPLY_RANDOM_PRESET_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_APPLY_EFFECT,
        apply_effect_service,
        schema=APPLY_EFFECT_SCHEMA,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DYNAMIC_SCENES,
        get_dynamic_scenes,
        supports_response=SupportsResponse.ONLY
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_DYNAMIC_SCENE,
        start_dynamic_scene,
        schema=START_DYNAMIC_SCENE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_DYNAMIC_SCENE,
        stop_dynamic_scene,
        schema=STOP_DYNAMIC_SCENE_SCHEMA
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_DYNAMIC_SCENES_FOR_TARGETS,
        stop_dynamic_scenes_for_targets,
        schema=STOP_DYNAMIC_SCENES_FOR_TARGETS_SCHEMA
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_ALL_DYNAMIC_SCENES,
        stop_all_dynamic_scenes,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_EXPORT_PRESETS,
        export_presets_service,
        supports_response=SupportsResponse.ONLY
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_IMPORT_PRESETS,
        import_presets_service,
        schema=IMPORT_PRESETS_SCHEMA,
        supports_response=SupportsResponse.ONLY
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GENERATE_EFFECT_PRESETS,
        generate_effect_presets_service,
        schema=GENERATE_EFFECT_PRESETS_SCHEMA,
        supports_response=SupportsResponse.ONLY
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_START_CIRCADIAN,
        start_circadian,
        schema=START_CIRCADIAN_SCHEMA
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP_CIRCADIAN,
        stop_circadian,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_SET_SCHEDULE,
        set_schedule,
        schema=SET_SCHEDULE_SCHEMA,
        supports_response=SupportsResponse.OPTIONAL
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_CLEAR_SCHEDULE,
        clear_schedule,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_SCHEDULE,
        get_schedule,
        supports_response=SupportsResponse.ONLY
    )


    return True

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    hass.data.setdefault(DOMAIN, {})["dynamic_scene_manager"] = DynamicSceneManager()

    await hass.async_add_executor_job(ensure_userdata_dirs)

    prefs_store = PrefsStore(hass)
    await prefs_store.async_load()
    hass.data[DOMAIN]["prefs_store"] = prefs_store

    schedule_store = Store(hass, SCHEDULE_STORE_VERSION, SCHEDULE_STORE_KEY)
    stored_schedule = await schedule_store.async_load() or {}
    hass.data[DOMAIN]["schedule_store"] = schedule_store
    hass.data[DOMAIN]["schedules"] = stored_schedule.get("schedules", [])
    hass.data[DOMAIN]["schedule_fired"] = set()

    await async_setup_view(hass)

    try:
        await hass.config_entries.async_forward_entry_setups(entry, ["scene"])
    except Exception:
        _LOGGER.exception("Scene Presets failed to set up the scene platform")

    async_setup_websocket_api(hass)

    watcher = PresetWatcher()

    async def _check_presets(now):
        if watcher.has_changed():
            errors = reload_preset_data()
            for error in errors:
                _LOGGER.error("Reloaded custom presets with errors: %s", error)
            async_dispatcher_send(hass, SIGNAL_PRESETS_CHANGED)

    hass.data[DOMAIN]["preset_watch_cancel"] = async_track_time_interval(
        hass, _check_presets, timedelta(seconds=30), name="scene_presets_watch"
    )

    async def _check_schedule(now):
        schedules = hass.data[DOMAIN].get("schedules", [])
        fired = hass.data[DOMAIN].setdefault("schedule_fired", set())
        for schedule_entry in due_entries(schedules, now, fired):
            fired.add(fired_key(schedule_entry, now))
            await _run_schedule_entry(hass, schedule_entry)

    hass.data[DOMAIN]["schedule_cancel"] = async_track_time_interval(
        hass, _check_schedule, timedelta(seconds=30), name="scene_presets_schedule"
    )

    return True

async def async_unload_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> bool:
    _stop_background(hass)

    unloaded = await hass.config_entries.async_unload_platforms(entry, ["scene"])

    await async_remove_view(hass)

    return unloaded

async def async_remove_entry(
    hass: HomeAssistant, entry: ConfigEntry
) -> None:

    _stop_background(hass)

    await async_remove_view(hass)