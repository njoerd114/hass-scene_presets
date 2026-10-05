import logging

from homeassistant.components.scene import Scene
from homeassistant.helpers.dispatcher import async_dispatcher_connect

from .const import SIGNAL_PRESETS_CHANGED
from .file_utils import PRESET_DATA
from .presets import apply_preset
from .scene_entities import build_scene_definitions
from .util import ensure_list, resolve_targets

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    added = set()
    entity_ids = entry.options.get("scene_targets") or []
    default_targets = {"entity_id": entity_ids} if entity_ids else None

    def add_definitions():
        definitions = build_scene_definitions(PRESET_DATA.get("presets", []), default_targets)
        new_entities = []

        for definition in definitions:
            if definition["unique_id"] in added:
                continue
            added.add(definition["unique_id"])
            new_entities.append(PresetScene(definition))

        if new_entities:
            async_add_entities(new_entities)

    add_definitions()
    entry.async_on_unload(async_dispatcher_connect(hass, SIGNAL_PRESETS_CHANGED, add_definitions))


class PresetScene(Scene):
    _attr_should_poll = False

    def __init__(self, definition):
        self._definition = definition
        self._attr_unique_id = definition["unique_id"]
        self._attr_name = definition["name"]
        self._attr_icon = definition["icon"]
        self._attr_available = definition["available"]

    async def async_activate(self, **kwargs):
        targets = self._definition["targets"]
        if not targets:
            _LOGGER.warning(
                "Scene '%s' has no targets configured and was not activated", self._attr_name
            )
            return

        transition = kwargs.get("transition", 1)
        entity_ids = ensure_list(targets.get("entity_id"))
        device_ids = ensure_list(targets.get("device_id"))
        area_ids = ensure_list(targets.get("area_id"))
        floor_ids = ensure_list(targets.get("floor_id"))
        label_ids = ensure_list(targets.get("label_id"))

        light_entity_ids = resolve_targets(
            self.hass, entity_ids, device_ids, area_ids, floor_ids, label_ids
        )

        if not light_entity_ids:
            _LOGGER.warning(
                "Scene '%s' has no matching light entities", self._attr_name
            )
            return

        await apply_preset(
            self.hass,
            self._definition["preset_id"],
            light_entity_ids,
            transition,
            False,
            False,
        )
