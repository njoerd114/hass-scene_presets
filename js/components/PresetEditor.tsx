import React, {useRef, useState} from "react";

import HaDialog from "./hass/building_blocks/HaDialog";
import HaButton from "./hass/building_blocks/HaButton";
import {Category} from "../types";
import {
    GeneratedPalette,
    extractPalette,
    generatePalettes,
    hexToRgb,
    hexToXy,
    refinePalette,
    rgbToHex,
} from "../colors";

const MAX_IMAGE_DIMENSION = 512;

type Mode = "manual" | "image" | "generator";

const labelStyle: React.CSSProperties = {
    display: "block",
    marginBottom: "0.35rem",
    fontFamily: "sans-serif",
    fontSize: "0.85rem",
    opacity: 0.85
};

const inputStyle: React.CSSProperties = {
    width: "100%",
    boxSizing: "border-box",
    padding: "0.6rem",
    borderRadius: "8px",
    border: "1px solid var(--divider-color, #cccccc)",
    backgroundColor: "var(--card-background-color, transparent)",
    color: "inherit",
    fontFamily: "sans-serif"
};

const colorInputStyle: React.CSSProperties = {
    width: "44px",
    height: "44px",
    padding: 0,
    border: "1px solid var(--divider-color, #cccccc)",
    borderRadius: "8px",
    cursor: "pointer",
    background: "none"
};

const chipStyle = (hex: string, selected: boolean): React.CSSProperties => ({
    width: "40px",
    height: "40px",
    borderRadius: "8px",
    background: hex,
    cursor: "pointer",
    padding: 0,
    border: selected ? "3px solid var(--primary-color, #03a9f4)" : "1px solid var(--divider-color, #cccccc)",
    boxShadow: selected ? "0 0 0 2px rgba(3,169,244,0.25)" : "none"
});

export const PresetEditor :React.FunctionComponent<{
    hass: any,
    categories: Array<Category>,
    onClose: () => void,
    onSaved: () => void,
}> = ({
    hass,
    categories,
    onClose,
    onSaved
}): React.JSX.Element => {
    const [name, setName] = useState<string>("");
    const [categoryId, setCategoryId] = useState<string>(categories[0]?.id ?? "");
    const [newCategory, setNewCategory] = useState<string>("");
    const [brightness, setBrightness] = useState<number>(200);
    const [colors, setColors] = useState<Array<string>>(["#ff9500"]);
    const [mode, setMode] = useState<Mode>("manual");
    const [pickerColor, setPickerColor] = useState<string>("#ff9500");
    const [seedColor, setSeedColor] = useState<string>("#ff9500");
    const [palettes, setPalettes] = useState<Array<GeneratedPalette>>([]);
    const [extractedColors, setExtractedColors] = useState<Array<string>>([]);
    const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
    const [saving, setSaving] = useState<boolean>(false);
    const [error, setError] = useState<string>("");

    const imageCanvasRef = useRef<HTMLCanvasElement | null>(null);

    const addColorHex = (hex: string) => {
        setColors((current) => (current.includes(hex) ? current : [...current, hex]));
    };

    const updateColor = (index: number, hex: string) => {
        setColors((current) => current.map((color, i) => (i === index ? hex : color)));
    };

    const removeColor = (index: number) => {
        setColors((current) => current.filter((_, i) => i !== index));
    };

    const toggleChip = (hex: string) => {
        setColors((current) => (current.includes(hex) ? current.filter((c) => c !== hex) : [...current, hex]));
    };

    const handleImage = (event: React.ChangeEvent<HTMLInputElement>) => {
        const file = event.target.files?.[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = () => {
            const dataUrl = String(reader.result);
            const image = new Image();
            image.onload = () => {
                const scale = Math.min(1, MAX_IMAGE_DIMENSION / Math.max(image.width, image.height));
                const canvas = document.createElement("canvas");
                canvas.width = Math.max(1, Math.round(image.width * scale));
                canvas.height = Math.max(1, Math.round(image.height * scale));

                const context = canvas.getContext("2d");
                if (!context) return;
                context.drawImage(image, 0, 0, canvas.width, canvas.height);

                const pixels = context.getImageData(0, 0, canvas.width, canvas.height).data;
                const extracted = refinePalette(extractPalette(pixels, 8)).map((color) => rgbToHex(color));

                imageCanvasRef.current = canvas;
                setExtractedColors(extracted);
                setColors(extracted);
                setImageDataUrl(canvas.toDataURL("image/jpeg", 0.85));
                setMode("image");
            };
            image.src = dataUrl;
        };
        reader.readAsDataURL(file);
    };

    const sampleImage = (event: React.MouseEvent<HTMLImageElement>) => {
        const canvas = imageCanvasRef.current;
        if (!canvas) return;

        const rect = event.currentTarget.getBoundingClientRect();
        const x = Math.min(canvas.width - 1, Math.max(0, Math.floor(((event.clientX - rect.left) / rect.width) * canvas.width)));
        const y = Math.min(canvas.height - 1, Math.max(0, Math.floor(((event.clientY - rect.top) / rect.height) * canvas.height)));

        const context = canvas.getContext("2d");
        if (!context) return;

        const [r, g, b] = context.getImageData(x, y, 1, 1).data;
        const hex = rgbToHex({r, g, b});
        addColorHex(hex);
        setExtractedColors((current) => (current.includes(hex) ? current : [...current, hex]));
    };

    const generate = () => {
        setPalettes(generatePalettes(hexToRgb(seedColor), 5));
        setMode("generator");
    };

    const save = async () => {
        if (!name.trim()) {
            setError("Please enter a name.");
            return;
        }
        if (colors.length === 0) {
            setError("Add at least one colour.");
            return;
        }

        setSaving(true);
        setError("");

        try {
            let imgFilename: string | undefined;

            if (imageDataUrl) {
                const content = imageDataUrl.split(",")[1] ?? "";
                const imageResult = await hass.callWS({
                    type: "scene_presets/save_preset_image",
                    filename: `${name.trim()}.jpg`,
                    content,
                });
                imgFilename = imageResult?.filename;
            }

            const preset: any = {
                name: name.trim(),
                bri: brightness,
                lights: colors.map((hex) => hexToXy(hex)),
            };
            if (categoryId) {
                preset.categoryId = categoryId;
            }
            if (imgFilename) {
                preset.img = imgFilename;
            }

            const response = await hass.callWS({
                type: "scene_presets/save_preset",
                preset,
                category_name: newCategory.trim() || undefined,
            });

            if (!response?.success) {
                setError((response?.errors || ["Failed to save preset."]).join(", "));
                setSaving(false);
                return;
            }

            onSaved();
            onClose();
        } catch (err: any) {
            setError(err?.message || "Failed to save preset.");
            setSaving(false);
        }
    };

    const tabStyle = (active: boolean): React.CSSProperties => ({
        flex: 1,
        padding: "0.55rem 0.75rem",
        borderRadius: "8px",
        border: "1px solid var(--divider-color, #cccccc)",
        background: active ? "var(--primary-color, #03a9f4)" : "transparent",
        color: active ? "#ffffff" : "inherit",
        cursor: "pointer",
        fontFamily: "sans-serif",
        fontSize: "0.9rem"
    });

    return (
        <HaDialog
            open={true}
            onClose={onClose}
            heading={"Create preset"}
        >
            <div
                style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "1rem",
                    width: "min(560px, 80vw)",
                    maxHeight: "68vh",
                    overflowY: "auto",
                    paddingRight: "0.25rem"
                }}
            >
                <div>
                    <span style={labelStyle}>Preset colours ({colors.length})</span>
                    <div style={{display: "flex", flexWrap: "wrap", gap: "0.5rem"}}>
                        {
                            colors.map((hex, index) => (
                                <span key={index} style={{position: "relative", display: "inline-block"}}>
                                    <input
                                        type={"color"}
                                        value={hex}
                                        aria-label={`Colour ${index + 1}`}
                                        onChange={(event) => updateColor(index, event.target.value)}
                                        style={colorInputStyle}
                                    />
                                    <button
                                        type={"button"}
                                        aria-label={"Remove colour"}
                                        onClick={() => removeColor(index)}
                                        style={{
                                            position: "absolute",
                                            top: "-8px",
                                            right: "-8px",
                                            width: "20px",
                                            height: "20px",
                                            borderRadius: "50%",
                                            border: "none",
                                            cursor: "pointer",
                                            background: "#ff5252",
                                            color: "#ffffff",
                                            lineHeight: "18px",
                                            fontSize: "13px"
                                        }}
                                    >×</button>
                                </span>
                            ))
                        }
                        {
                            colors.length === 0 &&
                            <span style={{fontFamily: "sans-serif", opacity: 0.6, fontSize: "0.85rem"}}>No colours yet</span>
                        }
                    </div>
                </div>

                <label>
                    <span style={labelStyle}>Name</span>
                    <input
                        type={"text"}
                        value={name}
                        placeholder={"My preset"}
                        onChange={(event) => setName(event.target.value)}
                        style={inputStyle}
                    />
                </label>

                <div style={{display: "flex", gap: "0.75rem"}}>
                    <label style={{flex: 1}}>
                        <span style={labelStyle}>Category</span>
                        <select
                            value={categoryId}
                            onChange={(event) => setCategoryId(event.target.value)}
                            style={inputStyle}
                        >
                            {
                                categories.map((category) => (
                                    <option key={category.id} value={category.id}>{category.name}</option>
                                ))
                            }
                        </select>
                    </label>
                    <label style={{flex: 1}}>
                        <span style={labelStyle}>…or new category</span>
                        <input
                            type={"text"}
                            value={newCategory}
                            placeholder={"My Presets"}
                            onChange={(event) => setNewCategory(event.target.value)}
                            style={inputStyle}
                        />
                    </label>
                </div>

                <label>
                    <span style={labelStyle}>Brightness — {brightness}</span>
                    <input
                        type={"range"}
                        min={0}
                        max={255}
                        value={brightness}
                        onChange={(event) => setBrightness(Number(event.target.value))}
                        style={{width: "100%"}}
                    />
                </label>

                <div style={{display: "flex", gap: "0.5rem"}}>
                    <button type={"button"} style={tabStyle(mode === "manual")} onClick={() => setMode("manual")}>Manual</button>
                    <button type={"button"} style={tabStyle(mode === "image")} onClick={() => setMode("image")}>From image</button>
                    <button type={"button"} style={tabStyle(mode === "generator")} onClick={() => setMode("generator")}>Generator</button>
                </div>

                {
                    mode === "manual" &&
                    <div style={{display: "flex", alignItems: "center", gap: "0.75rem"}}>
                        <input
                            type={"color"}
                            value={pickerColor}
                            aria-label={"Pick a colour"}
                            onChange={(event) => setPickerColor(event.target.value)}
                            style={colorInputStyle}
                        />
                        <HaButton label={"Add colour"} onClick={() => addColorHex(pickerColor)} />
                    </div>
                }

                {
                    mode === "image" &&
                    <div style={{display: "flex", flexDirection: "column", gap: "0.5rem"}}>
                        <input type={"file"} accept={"image/*"} onChange={handleImage} />
                        {
                            imageDataUrl &&
                            <img
                                src={imageDataUrl}
                                alt={"Selected"}
                                onClick={sampleImage}
                                title={"Click the picture to pick its colour"}
                                style={{maxWidth: "100%", borderRadius: "10px", cursor: "crosshair"}}
                            />
                        }
                        {
                            extractedColors.length > 0 &&
                            <>
                                <span style={labelStyle}>Tap a colour to add or remove it — or click the picture to sample a pixel</span>
                                <div style={{display: "flex", flexWrap: "wrap", gap: "0.5rem"}}>
                                    {
                                        extractedColors.map((hex) => (
                                            <button
                                                key={hex}
                                                type={"button"}
                                                aria-pressed={colors.includes(hex)}
                                                title={colors.includes(hex) ? "Remove colour" : "Add colour"}
                                                onClick={() => toggleChip(hex)}
                                                style={chipStyle(hex, colors.includes(hex))}
                                            />
                                        ))
                                    }
                                </div>
                                <div>
                                    <HaButton
                                        label={"Add all"}
                                        onClick={() => setColors((current) => {
                                            const merged = [...current];
                                            extractedColors.forEach((hex) => { if (!merged.includes(hex)) merged.push(hex); });
                                            return merged;
                                        })}
                                    />
                                </div>
                            </>
                        }
                    </div>
                }

                {
                    mode === "generator" &&
                    <div style={{display: "flex", flexDirection: "column", gap: "0.65rem"}}>
                        <div style={{display: "flex", alignItems: "center", gap: "0.75rem"}}>
                            <input
                                type={"color"}
                                value={seedColor}
                                aria-label={"Seed colour"}
                                onChange={(event) => setSeedColor(event.target.value)}
                                style={colorInputStyle}
                            />
                            <HaButton label={"Generate palettes"} onClick={generate} />
                        </div>
                        {
                            palettes.map((palette) => (
                                <div key={palette.name} style={{display: "flex", alignItems: "center", gap: "0.5rem", flexWrap: "wrap"}}>
                                    <span style={{minWidth: "8rem", fontFamily: "sans-serif", fontSize: "0.85rem"}}>{palette.name}</span>
                                    <div style={{display: "flex", gap: "0.3rem", flex: 1}}>
                                        {
                                            palette.colors.map((color, index) => {
                                                const hex = rgbToHex(color);
                                                const selected = colors.includes(hex);
                                                return (
                                                    <button
                                                        key={index}
                                                        type={"button"}
                                                        title={selected ? "Already added" : "Add colour"}
                                                        onClick={() => addColorHex(hex)}
                                                        style={{
                                                            width: "28px",
                                                            height: "28px",
                                                            borderRadius: "6px",
                                                            background: hex,
                                                            cursor: "pointer",
                                                            border: selected ? "3px solid var(--primary-color, #03a9f4)" : "1px solid var(--divider-color, #cccccc)"
                                                        }}
                                                    />
                                                );
                                            })
                                        }
                                    </div>
                                    <HaButton
                                        label={"Add all"}
                                        onClick={() => setColors((current) => {
                                            const merged = [...current];
                                            palette.colors.forEach((color) => {
                                                const hex = rgbToHex(color);
                                                if (!merged.includes(hex)) merged.push(hex);
                                            });
                                            return merged;
                                        })}
                                    />
                                </div>
                            ))
                        }
                    </div>
                }

                {
                    error &&
                    <div style={{color: "#ff5252", fontFamily: "sans-serif"}} role={"alert"}>{error}</div>
                }
                <div style={{display: "flex", justifyContent: "flex-end", gap: "0.5rem", marginTop: "0.25rem"}}>
                    <HaButton label={"Cancel"} variant={"secondary"} onClick={onClose} />
                    <HaButton label={saving ? "Saving…" : "Save preset"} onClick={save} disabled={saving} />
                </div>
            </div>
        </HaDialog>
    );
};
