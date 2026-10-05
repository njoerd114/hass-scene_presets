# Scene Presets

Hue-like scene presets for Home Assistant — no Hue bridge, no vendor lock-in, and no account required.

Scene Presets lets you save and apply colour presets to **any** `light` entity and exposes them through a sidebar panel and services, so they can be used in dashboards, automations, scripts and voice commands.

## Features

- **Any light**: apply colour presets to any colour-capable light, with automatic fallback to colour temperature or brightness-only lights.
- **Dynamic scenes**: continuously cycle a preset with smooth, smart-shuffled colour transitions.
- **WLED support**: native WLED presets, effects, palettes, speed and intensity.
- **Scene entities**: expose presets as native Home Assistant `scene` entities.
- **Circadian lighting** and time-of-day **scheduling**.
- **Import / export / share** custom presets, and auto-generate presets from a light's effects.
- **Server-side sync** of favourites, targets and tunables across devices.
- Fully local: no cloud, no account.

## Usage

Install via HACS, restart Home Assistant, then add the integration from **Settings → Devices & Services**. Presets can be applied from the **Scene Presets** sidebar panel or through the `scene_presets` services.

See the [README](https://github.com/njoerd114/hass-scene_presets#readme) and the [docs](https://github.com/njoerd114/hass-scene_presets/tree/master/docs) for details.
