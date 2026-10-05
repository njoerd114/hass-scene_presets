import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import config_validation as cv, selector
from .const import DOMAIN


class DomainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input):
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        return self.async_create_entry(
            title=DOMAIN,
            data={},
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return ScenePresetsOptionsFlow()


class ScenePresetsOptionsFlow(config_entries.OptionsFlow):
    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        "enable_server_sync",
                        default=self.config_entry.options.get("enable_server_sync", True),
                    ): cv.boolean,
                    vol.Optional(
                        "scene_targets",
                        default=self.config_entry.options.get("scene_targets", []),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="light", multiple=True)
                    ),
                }
            ),
        )