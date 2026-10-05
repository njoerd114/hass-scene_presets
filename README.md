<div align="center">
    <img src="assets/logo/github_banner.svg" width="600" alt="Scene Presets">
</div>

# Scene Presets

**Hue-like scene presets for Home Assistant.** Save colour presets and apply them to **any** `light` entity — with dynamic scenes, native WLED support, circadian lighting and scheduling. No bridge, no vendor lock-in, no account.

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=njoerd114&repository=hass-scene_presets&category=integration)
[![GitHub release](https://img.shields.io/github/v/release/njoerd114/hass-scene_presets?style=flat-square)](https://github.com/njoerd114/hass-scene_presets/releases)
[![License](https://img.shields.io/github/license/njoerd114/hass-scene_presets?style=flat-square)](./LICENSE)
[![HACS validate](https://github.com/njoerd114/hass-scene_presets/actions/workflows/hacs.yml/badge.svg)](https://github.com/njoerd114/hass-scene_presets/actions/workflows/hacs.yml)
[![Hassfest](https://github.com/njoerd114/hass-scene_presets/actions/workflows/hassfest.yml/badge.svg)](https://github.com/njoerd114/hass-scene_presets/actions/workflows/hassfest.yml)
[![CI](https://github.com/njoerd114/hass-scene_presets/actions/workflows/tests.yml/badge.svg)](https://github.com/njoerd114/hass-scene_presets/actions/workflows/tests.yml)

---

## Features

- **Works with any light** — colour-capable lights get full colour, tunable-white lights get a matching colour temperature, and dimmable lights get brightness.
- **Dynamic scenes** — endless loops that re-apply a preset with smooth, smart-shuffled colour transitions.
- **WLED support** — trigger native WLED presets, effects, palettes, speed and intensity, per segment.
- **Scene entities** — expose presets as native Home Assistant `scene` entities.
- **Circadian lighting** — adapt colour temperature and brightness to the sun throughout the day.
- **Scheduling** — apply presets at specific times and weekdays.
- **Import / export / share** — move custom presets between instances via JSON or a share code, and auto-generate presets from a light's effects.
- **Server-side sync** — optionally share favourites, targets and tunables across browsers and devices.
- **Fully local** — no cloud, no account, no external services.

## Requirements

- Home Assistant **2026.7.0** or newer.
- [HACS](https://hacs.xyz/) (recommended) for installation and updates.

## Installation

### HACS (recommended)

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=njoerd114&repository=hass-scene_presets&category=integration)

1. Click the button above (or in HACS use **⋮ → Custom repositories** and add `https://github.com/njoerd114/hass-scene_presets` as an **Integration**).
2. Search for **Scene Presets** in HACS and install it.
3. **Restart Home Assistant.**
4. Go to **Settings → Devices & Services → Add integration**, search for **Scene Presets** and confirm the wizard.

### Manual

1. Download the [latest release](https://github.com/njoerd114/hass-scene_presets/releases/latest).
2. Copy `custom_components/scene_presets` into your `<config>/custom_components/` directory.
3. **Restart Home Assistant.**
4. Add the integration from **Settings → Devices & Services**.

After setup you'll have a **Scene Presets** entry in the sidebar.

## Getting started

1. Open **Scene Presets** from the sidebar.
2. Under **Targets**, select the lights, devices, areas, floors or labels you want to control.
3. Optionally adjust **Tunables** (shuffle, custom brightness, custom transition, effect, distribution, transition style).
4. Click a preset tile to apply it.

The UI remembers your favourite presets, last targets and tunables. This is stored in your browser by default, or on the server if you enable **Server sync** in the integration options.

## Screenshots

![UI](./img/ui.png)

![Service call](./img/service.png)

![Last action payload](./img/last_action_payload.png)

## Dynamic scenes

Enable the **Dynamic** toggle to turn any preset into an endless loop that re-applies the preset with smart-shuffled colours every `interval`, using `transition` as the fade time.

- Active dynamic scenes appear at the top of the UI; tap one to stop it.
- A dynamic scene stops automatically once all its lights are turned off.
- Starting a dynamic scene stops overlapping ones.
- Long intervals and transitions produce the most subtle effect (and are gentler on Zigbee networks).
- Dynamic scenes intentionally do not survive a Home Assistant restart.

See [docs/Smart Shuffle.md](./docs/Smart%20Shuffle.md) for how smart shuffle avoids white flashes during transitions.

## WLED

For WLED lights, presets can trigger native WLED presets and control effects, palettes, speed and intensity per segment. The panel also offers an **Effect** picker and a generated **WLED Effects** category built from the effects your selected lights report.

## Services

Use the sidebar UI, then click the robot icon to copy a ready-to-paste service call — or call the services directly from automations, scripts, scenes and voice commands.

| Service | Description |
| --- | --- |
| `scene_presets.apply_preset` | Apply a preset to the given targets. |
| `scene_presets.apply_random_preset` | Apply a random preset, optionally limited to a category. |
| `scene_presets.apply_effect` | Apply a light effect (e.g. a WLED effect) to the given targets. |
| `scene_presets.start_dynamic_scene` | Start a looping dynamic scene. |
| `scene_presets.stop_dynamic_scene` | Stop a dynamic scene by ID. |
| `scene_presets.stop_dynamic_scenes_for_targets` | Stop all dynamic scenes touching the given targets. |
| `scene_presets.stop_all_dynamic_scenes` | Stop every running dynamic scene. |
| `scene_presets.get_dynamic_scenes` | Return all active dynamic scenes. |
| `scene_presets.start_circadian` / `stop_circadian` | Start/stop circadian lighting for the given targets. |
| `scene_presets.set_schedule` / `clear_schedule` / `get_schedule` | Manage scheduled presets. |
| `scene_presets.export_presets` / `import_presets` | Move custom presets between instances (JSON or share code). |
| `scene_presets.generate_effect_presets` | Create presets for every effect a set of lights reports. |

## Custom presets

You can add your own presets with a JSON file — categories, colours (CIE xy), images, brightness, effects, kelvin, white channel, WLED fields and scene targets are all supported.

- [docs/Custom Presets.md](./docs/Custom%20Presets.md)
- The full list of bundled presets and IDs lives in [assets](./custom_components/scene_presets/assets/Readme.md).

## Troubleshooting

- **No presets appear** — make sure at least one preset category is present and, if you use custom presets, that the JSON is valid. Invalid entries are logged and skipped.
- **A light does not change colour** — the light may only support colour temperature or brightness; Scene Presets falls back automatically.
- **Dynamic scene stopped by itself** — it stops when all its lights are off, when a new overlapping dynamic scene starts, or after a Home Assistant restart (by design).
- **The panel is empty** — try a hard refresh; the frontend also degrades gracefully if Home Assistant's frontend internals change.
- **Need logs** — enable debug logging for `custom_components.scene_presets` and check **Settings → System → Logs**.

## Support

- [Report an issue or request a feature](https://github.com/njoerd114/hass-scene_presets/issues)
- [Discussions](https://github.com/njoerd114/hass-scene_presets/discussions)

## License

See [LICENSE](./LICENSE).

---

This integration is a fork of [Hypfer/hass-scene_presets](https://github.com/Hypfer/hass-scene_presets), extended with WLED support, dynamic scenes, circadian lighting, scheduling, server-side sync and preset portability.
