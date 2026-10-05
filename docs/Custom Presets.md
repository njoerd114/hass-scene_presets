# Custom presets

Starting with v1.1.0, this integration also allows you to have your own custom presets.

Be advised though that this feature will not hold your hand. It is intended to be used by developers.

## How

On startup, the custom_component will create folder named `userdata/custom` inside `custom_components/scene_presets`
of your home assistant instance. By default, this folder will be empty apart from another folder named `assets`.

To add custom presets, you create a `presets.json` in that folder and add your custom images to that `assets` folder.
This essentially mirrors the structure of the included scenes. The JSON Schema is the same.
Everything in the custom presets will simply be added at the end of the lists of categories and presets.

Please note that there is no validation in place that would prevent you from creating ID conflicts nor is there any
validation ensuring that the schema of the custom data is correct. Just don't provide any incorrect data.

If I understood the HACS documentation correctly, this folder should survive component updates.<br/>
For now though, I'd recommend making backups just to be sure.

## Example

The best way to explain this feature is to give an example.

First the directory structure:

```
user@foo:/homeassistant/custom_components/scene_presets# tree userdata/
userdata/
└── custom
    ├── assets
    │ └── 1d2ef59e-8f29-4d58-a437-c0b03d90ce8a.jpeg
    └── presets.json

3 directories, 2 files
```

And here's the content of the `presets.json`:

```
{
  "categories": [
    {
      "name": "Color Temperatures",
      "id": "e0c17262-f84b-4943-bdd5-fcd24c574f24"
    }
  ],
  "presets": [
    {
      "id": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a",
      "categoryId": "e0c17262-f84b-4943-bdd5-fcd24c574f24",
      "name": "1800 Kelvin",
      "bri": 76,
      "lights": [
        {
          "x": 0.6264,
          "y": 0.3632
        }
      ]
    }
  ]
}
```

In there you can see a few things:

- We've added a new category named "Color Temperatures"
- We've added a single preset with the "Color Temperatures" categoryId 

  => every preset needs to be part of a category <br/>
  => custom presets can be part of stock categories <br/>
- The new "1800 Kelvin" preset has a single light

  => There is no limit to how many lights a preset can have <br/>
  => If you apply a preset to a group with more lights, some options will be repeated <br/>
  => Colors have to be specified as X/Y

After adding that example JSON and restarting Home Assistant, it looks like this:

![ex1.png](img/ex1.png)

And as you can see, we forgot to install Counter-Strike: Source.

To fix that, we need to change the preset to include an `img` key like this:

```
    {
      "id": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a",
      "categoryId": "e0c17262-f84b-4943-bdd5-fcd24c574f24",
      "name": "1800 Kelvin",
      "img": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a.jpeg"
      "bri": 76,
      "lights": [
        {
          "x": 0.6264,
          "y": 0.3632
        }
      ]
    }
```

This will now point to `userdata/custom/assets/1d2ef59e-8f29-4d58-a437-c0b03d90ce8a.jpeg`.<br/>
Make sure to place the desired image there.

## Effects

Presets may optionally define an `effect`, which is applied to any target light that supports it (for example WLED).<br/>
The value has to match one of the light's `effect_list` entries, otherwise it is ignored for that light.

```
    {
      "id": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a",
      "categoryId": "e0c17262-f84b-4943-bdd5-fcd24c574f24",
      "name": "WLED Rainbow",
      "effect": "Rainbow",
      "bri": 200,
      "lights": [
        {
          "x": 0.6264,
          "y": 0.3632
        }
      ]
    }
```

For a light that does not support effects, the preset still applies its color/brightness as usual.<br/>
The UI also exposes a `Custom Effect` override in the tunables section whenever the selected targets report any effects.

## WLED presets

A preset may also reference a saved WLED preset by name using `wled_preset`.<br/>
When applied to a WLED light, the `select` entity of the same device is set to that preset.

```
    {
      "id": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a",
      "categoryId": "e0c17262-f84b-4943-bdd5-fcd24c574f24",
      "name": "WLED Christmas",
      "wled_preset": "Christmas",
      "bri": 200,
      "lights": [
        {
          "x": 0.6264,
          "y": 0.3632
        }
      ]
    }
```

It is only applied when the device offers a preset with that exact name; otherwise it is ignored.<br/>
If a preset defines both `effect` and `wled_preset`, the WLED preset wins on WLED devices.

## WLED palette, speed and intensity

A preset may further define `wled_palette`, `wled_speed` (0-255) and `wled_intensity` (0-255).<br/>
These are applied to the matching `select`/`number` entities of the same WLED segment that the target light belongs to.

```
    {
      "id": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a",
      "categoryId": "e0c17262-f84b-4943-bdd5-fcd24c574f24",
      "name": "WLED Fire",
      "effect": "Fire 2012",
      "wled_palette": "Fire",
      "wled_speed": 128,
      "wled_intensity": 192,
      "bri": 200,
      "lights": [
        {
          "x": 0.6264,
          "y": 0.3632
        }
      ]
    }
```

## Color temperature and white channel

Instead of deriving a color temperature from the preset color, a preset may pin a `kelvin` value.<br/>
It is used for lights that support `color_temp` rather than an xy color mode.<br/>
For RGBW/RGBWW lights, a preset may also define a `white` channel (0-255) which is sent as `rgbw_color`/`rgbww_color`.

## Distribution and transition

A preset or service call may define `distribution` to control how preset colors are assigned to targets:
- `sequence` (default) - repeat the preset colors in order
- `balanced` - ensure every preset color is used before repeating
- `random` - pick a random color per target

`transition_style` controls the fade: `fade` (default, uses the transition duration) or `instant` (no fade).<br/>
Note that Home Assistant's light transition supports a duration only; arbitrary easing curves are not available.

## Scene entities

By adding an optional `targets` object to a preset, the integration also exposes it as a native Home Assistant
`scene` entity. Activating that scene applies the preset to the configured targets.

```
    {
      "id": "1d2ef59e-8f29-4d58-a437-c0b03d90ce8a",
      "categoryId": "e0c17262-f84b-4943-bdd5-fcd24c574f24",
      "name": "Evening",
      "icon": "mdi:weather-night",
      "targets": {
        "entity_id": "light.living_room"
      },
      "bri": 120,
      "lights": [
        {
          "x": 0.5264,
          "y": 0.4132
        }
      ]
    }
```

## Misc

To convert RGB colors to X/Y, you can use this js snippet using the `cie-rgb-color-converter` npm library:
```
const colorConverter = require("cie-rgb-color-converter");

const xyValue = colorConverter.rgbToXy(255, 126, 0);
xyValue.x = parseFloat(xyValue.x.toFixed(4));
xyValue.y = parseFloat(xyValue.y.toFixed(4));

console.log(JSON.stringify(xyValue, null, 2))
```