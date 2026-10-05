export type Rgb = { r: number; g: number; b: number };
export type Xy = { x: number; y: number };
export type Hsv = { h: number; s: number; v: number };
export type GeneratedPalette = { name: string; colors: Array<Rgb> };

const clamp = (value: number, min: number, max: number): number => Math.max(min, Math.min(max, value));

export const rgbToHex = ({r, g, b}: Rgb): string =>
    "#" + [r, g, b]
        .map((channel) => clamp(Math.round(channel), 0, 255).toString(16).padStart(2, "0"))
        .join("");

export const hexToRgb = (hex: string): Rgb => {
    const clean = hex.replace("#", "");
    const full = clean.length === 3 ? clean.split("").map((c) => c + c).join("") : clean;
    return {
        r: parseInt(full.slice(0, 2), 16) || 0,
        g: parseInt(full.slice(2, 4), 16) || 0,
        b: parseInt(full.slice(4, 6), 16) || 0,
    };
};

export const rgbToHsv = ({r, g, b}: Rgb): Hsv => {
    const rn = r / 255, gn = g / 255, bn = b / 255;
    const max = Math.max(rn, gn, bn);
    const min = Math.min(rn, gn, bn);
    const delta = max - min;
    let h = 0;

    if (delta !== 0) {
        if (max === rn) {
            h = ((gn - bn) / delta) % 6;
        } else if (max === gn) {
            h = (bn - rn) / delta + 2;
        } else {
            h = (rn - gn) / delta + 4;
        }
        h *= 60;
        if (h < 0) {
            h += 360;
        }
    }

    return {h, s: max === 0 ? 0 : delta / max, v: max};
};

export const hsvToRgb = ({h, s, v}: Hsv): Rgb => {
    const c = v * s;
    const x = c * (1 - Math.abs(((h / 60) % 2) - 1));
    const m = v - c;
    let rn = 0, gn = 0, bn = 0;

    if (h < 60) { rn = c; gn = x; }
    else if (h < 120) { rn = x; gn = c; }
    else if (h < 180) { gn = c; bn = x; }
    else if (h < 240) { gn = x; bn = c; }
    else if (h < 300) { rn = x; bn = c; }
    else { rn = c; bn = x; }

    return {r: Math.round((rn + m) * 255), g: Math.round((gn + m) * 255), b: Math.round((bn + m) * 255)};
};

export const rgbToXy = ({r, g, b}: Rgb): Xy => {
    const lin = (value: number): number => {
        const c = value / 255;
        return c <= 0.04045 ? c / 12.92 : Math.pow((c + 0.055) / 1.055, 2.4);
    };
    const R = lin(r), G = lin(g), B = lin(b);
    const X = R * 0.4124 + G * 0.3576 + B * 0.1805;
    const Y = R * 0.2126 + G * 0.7152 + B * 0.0722;
    const Z = R * 0.0193 + G * 0.1192 + B * 0.9505;
    const sum = X + Y + Z || 1;
    return {x: +(X / sum).toFixed(4), y: +(Y / sum).toFixed(4)};
};

export const xyToRgb = ({x, y}: Xy): Rgb => {
    const z = 1 - x - y;
    const r = x * 3.2406 - y * 1.5372 - z * 0.4986;
    const g = -x * 0.9689 + y * 1.8758 + z * 0.0415;
    const b = x * 0.0557 - y * 0.2040 + z * 1.0570;
    const gamma = (channel: number): number => {
        const value = channel <= 0.0031308 ? 12.92 * channel : 1.055 * Math.pow(channel, 1 / 2.4) - 0.055;
        return Math.round(clamp(value, 0, 1) * 255);
    };
    return {r: gamma(r), g: gamma(g), b: gamma(b)};
};

export const hexToXy = (hex: string): Xy => rgbToXy(hexToRgb(hex));
export const xyToHex = (xy: Xy): string => rgbToHex(xyToRgb(xy));

export const colorDistance = (a: Rgb, b: Rgb): number =>
    Math.sqrt((a.r - b.r) ** 2 + (a.g - b.g) ** 2 + (a.b - b.b) ** 2);

export const distinctColors = (colors: Array<Rgb>, minDistance = 45): Array<Rgb> => {
    const kept: Array<Rgb> = [];
    for (const color of colors) {
        if (kept.every((existing) => colorDistance(existing, color) >= minDistance)) {
            kept.push(color);
        }
    }
    return kept;
};

export const isLightingRelevant = (color: Rgb): boolean => {
    const {s, v} = rgbToHsv(color);
    return s >= 0.15 && v >= 0.08;
};

export const refinePalette = (colors: Array<Rgb>): Array<Rgb> =>
    distinctColors(colors.filter(isLightingRelevant));

const channelRange = (bucket: Array<Rgb>): {range: number; channel: "r" | "g" | "b"} => {
    let range = 0;
    let channel: "r" | "g" | "b" = "r";
    for (const key of ["r", "g", "b"] as const) {
        let min = 255, max = 0;
        for (const color of bucket) {
            if (color[key] < min) min = color[key];
            if (color[key] > max) max = color[key];
        }
        if (max - min > range) {
            range = max - min;
            channel = key;
        }
    }
    return {range, channel};
};

const averageColor = (bucket: Array<Rgb>): Rgb => {
    const total = bucket.reduce(
        (acc, color) => ({r: acc.r + color.r, g: acc.g + color.g, b: acc.b + color.b}),
        {r: 0, g: 0, b: 0}
    );
    return {
        r: Math.round(total.r / bucket.length),
        g: Math.round(total.g / bucket.length),
        b: Math.round(total.b / bucket.length),
    };
};

export const extractPalette = (data: Uint8ClampedArray, count: number): Array<Rgb> => {
    const pixels: Array<Rgb> = [];
    for (let i = 0; i < data.length; i += 4) {
        if (data[i + 3] < 125) continue;
        pixels.push({r: data[i], g: data[i + 1], b: data[i + 2]});
    }

    if (pixels.length === 0 || count <= 0) {
        return [];
    }

    const buckets: Array<Array<Rgb>> = [pixels];
    while (buckets.length < count) {
        let targetIndex = -1;
        let largest = 0;

        buckets.forEach((bucket, index) => {
            if (bucket.length < 2) return;
            const {range} = channelRange(bucket);
            if (range > largest) {
                largest = range;
                targetIndex = index;
            }
        });

        if (targetIndex === -1) break;

        const bucket = buckets[targetIndex];
        const {channel} = channelRange(bucket);
        bucket.sort((a, b) => a[channel] - b[channel]);
        const mid = Math.floor(bucket.length / 2);
        buckets.splice(targetIndex, 1, bucket.slice(0, mid), bucket.slice(mid));
    }

    return buckets.map((bucket) => averageColor(bucket));
};

export const generatePalettes = (seed: Rgb, count = 4): Array<GeneratedPalette> => {
    const {h, s, v} = rgbToHsv(seed);
    const baseS = clamp(s, 0.45, 1);
    const baseV = clamp(v, 0.6, 1);
    const size = Math.max(3, Math.min(count, 5));
    const spread = (start: number, step: number, length: number): Array<number> =>
        Array.from({length}, (_, index) => start + step * index);

    const make = (hues: Array<number>, name: string): GeneratedPalette => ({
        name,
        colors: hues.map((hue) => hsvToRgb({h: ((hue % 360) + 360) % 360, s: baseS, v: baseV})),
    });

    const monochromatic: GeneratedPalette = {
        name: "Monochromatic",
        colors: Array.from({length: size}, (_, index) =>
            hsvToRgb({h, s: clamp(baseS - index * 0.12, 0.35, 1), v: clamp(baseV - index * 0.08, 0.4, 1)})
        ),
    };

    return [
        make(spread(h - 45, 45, size), "Analogous"),
        make([h, h + 180, ...spread(h - 30, 30, size - 2)], "Complementary"),
        make([h, h + 150, h + 210], "Split complementary"),
        make(spread(h, 120, 3), "Triadic"),
        make(spread(h, 90, 4), "Tetradic"),
        monochromatic,
    ].map((palette) => ({...palette, colors: refinePalette(palette.colors)}))
        .filter((palette) => palette.colors.length >= 2);
};
