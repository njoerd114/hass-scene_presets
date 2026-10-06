# Circadian lighting

Circadian lighting adapts the colour temperature and brightness of your lights to the position of the sun, so that lights are cooler and brighter during the day and warmer and dimmer in the evening.

Scene Presets exposes this through two services, `scene_presets.start_circadian` and `scene_presets.stop_circadian`. There is no panel UI for it, so you drive it from automations, scripts or voice commands like any other service.

A few things worth knowing up front:

- It only updates lights that are currently on. Lights that are off are left alone.
- It is not persistent. It does not survive a Home Assistant restart or a reload of the integration. To keep it running, start it again from an automation on startup.
- It is service-only. There is nothing to configure in the sidebar; every option is a service field.

## Built-in engine

By default, Scene Presets computes the curve itself from the sun's elevation:

1. The sun elevation is mapped to a position between `-1` (well below the horizon) and `+1` (high in the sky), with `0` at the horizon.
2. Colour temperature interpolates between `min_kelvin` at the horizon and `max_kelvin` at solar noon, and drops towards `sleep_kelvin` deep at night.
3. Brightness stays at `max_brightness` while the sun is up and ramps down towards `min_brightness` overnight.
4. The values are re-applied every `interval` seconds.

```yaml
service: scene_presets.start_circadian
data:
  targets:
    area_id: living_room
  min_kelvin: 3000
  max_kelvin: 6500
  sleep_kelvin: 1900
  min_brightness: 1
  max_brightness: 100
  interval: 60
```

To stop it:

```yaml
service: scene_presets.stop_circadian
```

## Using Adaptive Lighting instead

If you already run the [Adaptive Lighting](https://adaptive-lighting.nijho.lt/) custom integration and have tuned it (sunrise and sunset offsets, sleep mode, brightness mode and so on), you can tell Scene Presets to read the curve from one of its switches instead of computing its own:

```yaml
service: scene_presets.start_circadian
data:
  targets:
    entity_id:
      - light.hallway
      - light.landing
  adaptive_lighting_switch: switch.adaptive_lighting_living_room
```

When `adaptive_lighting_switch` is set, Scene Presets reads the `color_temp_kelvin` and `brightness_pct` attributes from that switch and applies them to your targets. It reacts whenever the Adaptive Lighting switch updates those attributes, and the `interval` timer is kept as a fallback.

### Fallback

If the Adaptive Lighting switch is off, missing, or reports no usable values, Scene Presets silently falls back to its built-in engine and logs a single info message. It never stops unexpectedly.

### What it does not do

- It applies values only to the targets you pass. It does not call any `adaptive_lighting.*` service and does not change your Adaptive Lighting settings.
- It does not set manual control on Adaptive Lighting.
- If one of your targets is also managed by that same Adaptive Lighting switch, both will write to it. Use this mode to mirror Adaptive Lighting's curve onto lights that Adaptive Lighting does not manage.

## Service fields

### `scene_presets.start_circadian`

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `targets` | target | — | What to adapt (entities, devices, areas, floors or labels). Required. |
| `min_kelvin` | int (1000–10000) | `3000` | Warmest colour temperature, at the horizon. |
| `max_kelvin` | int (1000–10000) | `6500` | Coolest colour temperature, at solar noon. |
| `sleep_kelvin` | int (1000–10000) | `1900` | Colour temperature in deep night. |
| `min_brightness` | int (0–100) | `1` | Minimum brightness percentage. |
| `max_brightness` | int (0–100) | `100` | Maximum brightness percentage. |
| `interval` | int (5–86400) | `60` | How often the values are re-applied, in seconds. |
| `adaptive_lighting_switch` | entity id | — | Optional. Read the curve from this Adaptive Lighting switch instead of the built-in engine. |

`min_kelvin`, `max_kelvin`, `sleep_kelvin`, `min_brightness`, `max_brightness` and `interval` are ignored while `adaptive_lighting_switch` is set and available.

### `scene_presets.stop_circadian`

Stops the circadian loop. Takes no fields.

## Example automations

Start at sunrise and stop at bedtime, using the built-in engine:

```yaml
automation:
  - alias: Circadian lighting on at sunrise
    triggers:
      - trigger: sun
        event: sunrise
    actions:
      - service: scene_presets.start_circadian
        data:
          targets:
            area_id: living_room
          interval: 60

  - alias: Circadian lighting off at bedtime
    triggers:
      - trigger: time
        at: "23:00:00"
    actions:
      - service: scene_presets.stop_circadian
```

Because circadian lighting is not persistent, start it again after a restart:

```yaml
automation:
  - alias: Restore circadian lighting on start
    triggers:
      - trigger: homeassistant
        event: start
    actions:
      - service: scene_presets.start_circadian
        data:
          targets:
            area_id: living_room
```
