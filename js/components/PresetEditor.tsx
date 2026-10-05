import React, {useState} from "react";

import HaDialog from "./hass/building_blocks/HaDialog";
import MwcButton from "./hass/building_blocks/MwcButton";
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
    const [imageDataUrl, setImageDataUrl] = useState<string | null>(null);
    const [saving, setSaving] = useState<boolean>(false);
    const [error, setError] = useState<string>("");

    const addColor = () => {
        setColors((current) => [...current, pickerColor]);
    };

    const removeColor = (index: number) => {
        setColors((current) => current.filter((_, i) => i !== index));
    };

    const usePalette = (palette: GeneratedPalette) => {
        setColors(palette.colors.map((color) => rgbToHex(color)));
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
                const extracted = refinePalette(extractPalette(pixels, 6));

                if (extracted.length > 0) {
                    setColors(extracted.map((color) => rgbToHex(color)));
                }
                setImageDataUrl(canvas.toDataURL("image/jpeg", 0.85));
                setMode("image");
            };
            image.src = dataUrl;
        };
        reader.readAsDataURL(file);
    };

    const generate = () => {
        setPalettes(generatePalettes(hexToRgb(seedColor), 4));
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
        padding: "0.5rem 0.9rem",
        marginRight: "0.35rem",
        borderRadius: "8px",
        border: "1px solid var(--divider-color, #cccccc)",
        background: active ? "var(--primary-color, #03a9f4)" : "transparent",
        color: active ? "#ffffff" : "inherit",
        cursor: "pointer",
        fontFamily: "sans-serif"
    });

    return (
        <HaDialog
            open={true}
            onClose={onClose}
            heading={"Create preset"}
        >
            <div style={{display: "flex", flexDirection: "column", gap: "0.75rem", minWidth: "360px"}}>
                <label>
                    <span style={{display: "block", marginBottom: "0.25rem"}}>Name</span>
                    <input
                        type={"text"}
                        value={name}
                        onChange={(event) => setName(event.target.value)}
                        style={{width: "100%", padding: "0.5rem"}}
                    />
                </label>

                <label>
                    <span style={{display: "block", marginBottom: "0.25rem"}}>Category</span>
                    <select
                        value={categoryId}
                        onChange={(event) => setCategoryId(event.target.value)}
                        style={{width: "100%", padding: "0.5rem"}}
                    >
                        {
                            categories.map((category) => (
                                <option key={category.id} value={category.id}>{category.name}</option>
                            ))
                        }
                    </select>
                </label>

                <label>
                    <span style={{display: "block", marginBottom: "0.25rem"}}>New category (optional)</span>
                    <input
                        type={"text"}
                        value={newCategory}
                        placeholder={"e.g. My Presets"}
                        onChange={(event) => setNewCategory(event.target.value)}
                        style={{width: "100%", padding: "0.5rem"}}
                    />
                </label>

                <label>
                    <span style={{display: "block", marginBottom: "0.25rem"}}>Brightness ({brightness})</span>
                    <input
                        type={"range"}
                        min={0}
                        max={255}
                        value={brightness}
                        onChange={(event) => setBrightness(Number(event.target.value))}
                        style={{width: "100%"}}
                    />
                </label>

                <div>
                    <button type={"button"} style={tabStyle(mode === "manual")} onClick={() => setMode("manual")}>Manual</button>
                    <button type={"button"} style={tabStyle(mode === "image")} onClick={() => setMode("image")}>From image</button>
                    <button type={"button"} style={tabStyle(mode === "generator")} onClick={() => setMode("generator")}>Generator</button>
                </div>

                {
                    mode === "manual" &&
                    <div style={{display: "flex", alignItems: "center", gap: "0.5rem"}}>
                        <input type={"color"} value={pickerColor} onChange={(event) => setPickerColor(event.target.value)} />
                        <MwcButton label={"Add colour"} onClick={addColor} />
                    </div>
                }

                {
                    mode === "image" &&
                    <div>
                        <input type={"file"} accept={"image/*"} onChange={handleImage} />
                        {imageDataUrl && <img src={imageDataUrl} alt={"Selected"} style={{maxWidth: "100%", marginTop: "0.5rem", borderRadius: "8px"}} />}
                    </div>
                }

                {
                    mode === "generator" &&
                    <div style={{display: "flex", flexDirection: "column", gap: "0.5rem"}}>
                        <div style={{display: "flex", alignItems: "center", gap: "0.5rem"}}>
                            <input type={"color"} value={seedColor} onChange={(event) => setSeedColor(event.target.value)} />
                            <MwcButton label={"Generate palettes"} onClick={generate} />
                        </div>
                        {
                            palettes.map((palette) => (
                                <div key={palette.name} style={{display: "flex", alignItems: "center", gap: "0.5rem"}}>
                                    <span style={{minWidth: "9rem", fontFamily: "sans-serif", fontSize: "0.85rem"}}>{palette.name}</span>
                                    <div style={{display: "flex", gap: "0.25rem", flex: 1}}>
                                        {
                                            palette.colors.map((color, index) => (
                                                <span
                                                    key={index}
                                                    style={{width: "24px", height: "24px", borderRadius: "4px", background: rgbToHex(color)}}
                                                />
                                            ))
                                        }
                                    </div>
                                    <MwcButton label={"Use"} onClick={() => usePalette(palette)} />
                                </div>
                            ))
                        }
                    </div>
                }

                <div>
                    <span style={{display: "block", marginBottom: "0.25rem"}}>Colours ({colors.length})</span>
                    <div style={{display: "flex", flexWrap: "wrap", gap: "0.5rem"}}>
                        {
                            colors.map((hex, index) => (
                                <span
                                    key={index}
                                    role={"button"}
                                    tabIndex={0}
                                    title={"Remove"}
                                    onClick={() => removeColor(index)}
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter" || event.key === " ") {
                                            event.preventDefault();
                                            removeColor(index);
                                        }
                                    }}
                                    style={{
                                        width: "40px",
                                        height: "40px",
                                        borderRadius: "8px",
                                        background: hex,
                                        cursor: "pointer",
                                        border: "1px solid var(--divider-color, #cccccc)"
                                    }}
                                />
                            ))
                        }
                    </div>
                </div>

                {
                    error &&
                    <div style={{color: "#ff5252", fontFamily: "sans-serif"}} role={"alert"}>{error}</div>
                }
            </div>

            <MwcButton
                label={"Cancel"}
                onClick={onClose}
                slot={"secondaryAction"}
            />
            <MwcButton
                label={saving ? "Saving…" : "Save preset"}
                onClick={save}
                slot={"primaryAction"}
            />
        </HaDialog>
    );
};
