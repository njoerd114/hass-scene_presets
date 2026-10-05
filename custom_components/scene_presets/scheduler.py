import asyncio
import logging

from .circadian import brightness_pct, color_temp_kelvin, elevation_to_position

_LOGGER = logging.getLogger(__name__)


def circadian_command(config, position):
    kelvin = color_temp_kelvin(
        position,
        config.get("min_kelvin", 3000),
        config.get("max_kelvin", 6500),
        config.get("sleep_kelvin", 1900),
    )
    pct = brightness_pct(
        position,
        config.get("min_brightness", 1),
        config.get("max_brightness", 100),
    )
    brightness = max(1, min(255, round(pct * 255 / 100)))

    return {"color_temp_kelvin": kelvin, "brightness": brightness}


class SceneScheduler:
    def __init__(self, hass):
        self.hass = hass
        self._cancel = None
        self._config = None

    def start(self, config):
        self.stop()

        from homeassistant.helpers.event import async_track_time_interval
        from datetime import timedelta

        self._config = config
        self._cancel = async_track_time_interval(
            self.hass,
            self._tick,
            timedelta(seconds=config.get("interval", 60)),
            name="scene_presets_circadian",
        )
        self.hass.async_create_task(self._tick(None))

    def stop(self):
        if self._cancel is not None:
            self._cancel()
            self._cancel = None
        self._config = None

    @property
    def running(self):
        return self._cancel is not None

    async def _tick(self, now):
        config = self._config
        if not config:
            return

        sun = self.hass.states.get("sun.sun")
        elevation = sun.attributes.get("elevation", 0.0) if sun else 0.0
        command = circadian_command(config, elevation_to_position(elevation))

        tasks = []
        for entity_id in config.get("light_entity_ids", []):
            state = self.hass.states.get(entity_id)
            if state is None or state.state != "on":
                continue
            tasks.append(
                self.hass.services.async_call(
                    "light",
                    "turn_on",
                    {"entity_id": entity_id, **command},
                    blocking=False,
                )
            )

        if tasks:
            await asyncio.gather(*tasks)
