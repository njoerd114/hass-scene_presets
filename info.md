# Scene Presets

Hue-like scene presets for Home Assistant — no Hue bridge, no vendor lock-in, and no account required.

Scene Presets lets you save and apply colour presets to **any** `light` entity and exposes them through a sidebar panel and services, so they can be used in dashboards, automations, scripts and voice commands.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=njoerd114&repository=hass-scene_presets&category=integration)

## Features

- **Any light**: apply colour presets to any colour-capable light, with automatic fallback to colour temperature or brightness-only lights.
- **Dynamic scenes**: continuously cycle a preset with smooth, smart-shuffled colour transitions.
- **WLED support**: native WLED presets, effects, palettes, speed and intensity.
- **Scene entities**: expose presets as native Home Assistant `scene` entities.
- **Circadian lighting** (built-in, or driven by [Adaptive Lighting](https://adaptive-lighting.nijho.lt/)) and time-of-day **scheduling**.
- **Import / export / share** custom presets, and auto-generate presets from a light's effects.
- **Server-side sync** of favourites, targets and tunables across devices.
- Fully local: no cloud, no account.

## Installation

1. Click the button above, or add `https://github.com/njoerd114/hass-scene_presets` to **HACS → ⋮ → Custom repositories** as an **Integration**.
2. Install **Scene Presets** from HACS and **restart Home Assistant**.
3. Add it from **Settings → Devices & Services → Add integration → Scene Presets**.

Requires Home Assistant **2026.7.0** or newer.

## Documentation

- [README](https://github.com/njoerd114/hass-scene_presets#readme)
- [Custom presets](https://github.com/njoerd114/hass-scene_presets/blob/master/docs/Custom%20Presets.md)
- [Circadian lighting](https://github.com/njoerd114/hass-scene_presets/blob/master/docs/Circadian%20Lighting.md)
- [Report an issue](https://github.com/njoerd114/hass-scene_presets/issues)
