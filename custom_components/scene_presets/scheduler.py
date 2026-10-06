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


def adaptive_lighting_command(state):
    if state is None or getattr(state, "state", None) != "on":
        return None

    attributes = getattr(state, "attributes", None) or {}
    kelvin = attributes.get("color_temp_kelvin")
    pct = attributes.get("brightness_pct")
    if kelvin is None or pct is None:
        return None

    try:
        brightness = max(1, min(255, round(float(pct) * 255 / 100)))
        return {"color_temp_kelvin": int(kelvin), "brightness": brightness}
    except (TypeError, ValueError):
        return None


class SceneScheduler:
    def __init__(self, hass):
        self.hass = hass
        self._cancel = None
        self._al_cancel = None
        self._config = None
        self._fallback_logged = False

    def start(self, config):
        self.stop()

        from homeassistant.helpers.event import async_track_time_interval
        from datetime import timedelta

        self._config = config
        al_switch = self._al_switch()
        if al_switch:
            from homeassistant.helpers.event import async_track_state_change_event

            self._al_cancel = async_track_state_change_event(
                self.hass,
                al_switch,
                self._al_changed,
            )

        self._cancel = async_track_time_interval(
            self.hass,
            self._fallback_tick,
            timedelta(seconds=config.get("interval", 60)),
            name="scene_presets_circadian",
        )
        self.hass.async_create_task(self._tick(None))

    def stop(self):
        if self._al_cancel is not None:
            self._al_cancel()
            self._al_cancel = None
        if self._cancel is not None:
            self._cancel()
            self._cancel = None
        self._config = None
        self._fallback_logged = False

    @property
    def running(self):
        return self._cancel is not None or self._al_cancel is not None

    def _al_switch(self):
        config = self._config
        if not config:
            return None
        return config.get("adaptive_lighting_switch")

    def _al_command(self):
        al_switch = self._al_switch()
        if not al_switch:
            return None
        return adaptive_lighting_command(self.hass.states.get(al_switch))

    def _builtin_command(self):
        config = self._config or {}

        sun = self.hass.states.get("sun.sun")
        elevation = sun.attributes.get("elevation", 0.0) if sun else 0.0
        return circadian_command(config, elevation_to_position(elevation))

    def _command(self):
        command = self._al_command()
        if command is not None:
            return command

        if self._al_switch() and not self._fallback_logged:
            _LOGGER.info(
                "Adaptive Lighting switch unavailable or off; using built-in circadian engine"
            )
            self._fallback_logged = True

        return self._builtin_command()

    async def _apply(self, command):
        config = self._config
        if not config:
            return

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

    async def _tick(self, now):
        if not self._config:
            return

        await self._apply(self._command())

    async def _fallback_tick(self, now):
        if not self._config:
            return
        if self._al_command() is not None:
            return
        await self._tick(now)

    async def _al_changed(self, event):
        if not self._config:
            return
        await self._tick(event)
