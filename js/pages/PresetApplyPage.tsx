import React, {useEffect, useMemo, useRef, useState} from "react";
import {PresetTile} from "../components/PresetTile";
import {useLocalStorage} from "../hooks/useLocalStorage";
import {STORAGE_ERROR_EVENT, getLastStorageError} from "../hooks/storageErrors";
import HaSwitch from "../components/hass/building_blocks/HaSwitch";
import {HaTargetSelector, HaTargetSelectorValue} from "../components/hass/selectors/HaTargetSelector";
import {HaNumberSelector} from "../components/hass/selectors/HaNumberSelector";
import {HaSelect} from "../components/hass/selectors/HaSelect";
import HaIconButton from "../components/hass/building_blocks/HaIconButton";
import {Category, Preset} from "../types";
import HaDialog from "../components/hass/building_blocks/HaDialog";
import HaButton from "../components/hass/building_blocks/HaButton";
import {DynamicSceneTile} from "../components/DynamicSceneTile";
import {CategoryTiles} from "../components/CategoryTiles";
import {PresetEditor} from "../components/PresetEditor";
import {presetImageUrl} from "../helpers";

const DEFAULT_TUNABLE_SETTINGS = {
    shuffle: false,
    smartShuffle: false,
    customBrightness: false,
    customBrightnessValue: 128,
    customTransition: false,
    customTransitionValue: 60,
    customEffect: false,
    effectValue: "",

    dynamic: false,
    dynamicTransitionValue: 45,
    dynamicIntervalValue: 60,
};

const DYNAMIC_SCENE_REFRESH_INTERVAL = 30*1000;

export const Switch :React.FunctionComponent<{
    label: string,
    value: boolean,
    setValue: (newValue: boolean) => void
}> = ({
    label,
    value,
    setValue
}): React.JSX.Element => {
    return (
        <label
            style={{
                lineHeight: "3rem"
            }}
        >
            <span style={{marginRight: "0.5rem"}}>{label}</span>
            <HaSwitch
                value={value}
                onValueChanged={(value) => {
                    setValue(value);
                }}
            />
        </label>
    );
};


export const OptionalNumberSelector :React.FunctionComponent<{
    label: string,
    enabled: boolean,
    setEnabled: (newValue: boolean) => void,
    value: number,
    setValue: (newValue: number) => void,
    minValue: number,
    maxValue: number,
    hass: any,
    extraSelectorProps?: any
}> = ({
    label,
    enabled,
    setEnabled,
    value,
    setValue,
    minValue,
    maxValue,
    hass,
    extraSelectorProps = {}
}): React.JSX.Element => {
    return (
        <label
            style={{
                lineHeight: "3rem"
            }}
        >
            <span style={{marginRight: "0.5rem"}}>{label}</span>
            <HaSwitch
                value={enabled}
                onValueChanged={(value) => {
                    setEnabled(value);
                }}
            />
            {
                enabled &&
                <div
                    style={{
                        maxWidth: "540px"
                    }}
                >
                    <HaNumberSelector
                        hass={hass}
                        selector={{
                            "number": {
                                "min": minValue,
                                "max": maxValue,

                                ...extraSelectorProps
                            }
                        }}
                        value={value}
                        onValueChanged={(value: number) => {
                            setValue(value);
                        }}
                    />
                </div>
            }
        </label>
    );
};

export const OptionalSelect :React.FunctionComponent<{
    label: string,
    enabled: boolean,
    setEnabled: (newValue: boolean) => void,
    value: string,
    setValue: (newValue: string) => void,
    options: Array<string>,
    hass: any
}> = ({
    label,
    enabled,
    setEnabled,
    value,
    setValue,
    options,
    hass
}): React.JSX.Element => {
    return (
        <label
            style={{
                lineHeight: "3rem"
            }}
        >
            <span style={{marginRight: "0.5rem"}}>{label}</span>
            <HaSwitch
                value={enabled}
                onValueChanged={(value) => {
                    setEnabled(value);
                }}
            />
            {
                enabled &&
                <div
                    style={{
                        maxWidth: "540px"
                    }}
                >
                    <HaSelect
                        hass={hass}
                        selector={{
                            "select": {
                                "options": options
                            }
                        }}
                        value={value}
                        onValueChanged={(value: string) => {
                            setValue(value);
                        }}
                    />
                </div>
            }
        </label>
    );
};

export const LabeledSelect :React.FunctionComponent<{
    label: string,
    value: string,
    setValue: (newValue: string) => void,
    options: Array<string>,
    hass: any
}> = ({
    label,
    value,
    setValue,
    options,
    hass
}): React.JSX.Element => {
    return (
        <label
            style={{
                lineHeight: "3rem"
            }}
        >
            <span style={{marginRight: "0.5rem"}}>{label}</span>
            <div
                style={{
                    maxWidth: "540px"
                }}
            >
                <HaSelect
                    hass={hass}
                    selector={{
                        "select": {
                            "options": options
                        }
                    }}
                    value={value}
                    onValueChanged={(value: string) => {
                        setValue(value);
                    }}
                />
            </div>
        </label>
    );
};

export const NumberSelector :React.FunctionComponent<{
    label: string,
    value: number,
    setValue: (newValue: number) => void,
    minValue: number,
    maxValue: number,
    hass: any,
    extraSelectorProps?: any
}> = ({
    label,
    value,
    setValue,
    minValue,
    maxValue,
    hass,
    extraSelectorProps = {}
}): React.JSX.Element => {
    return (
        <label
            style={{
                lineHeight: "3rem"
            }}
        >
            <span style={{marginRight: "0.5rem"}}>{label}</span>

            <div
                style={{
                    maxWidth: "540px"
                }}
            >
                <HaNumberSelector
                    hass={hass}
                    selector={{
                        "number": {
                            "min": minValue,
                            "max": maxValue,

                            ...extraSelectorProps
                        }
                    }}
                    value={value}
                    onValueChanged={(value: number) => {
                        setValue(value);
                    }}
                />
            </div>
        </label>
    );
};



export const PresetApplyPage: React.FunctionComponent<{
    hass: any,
    categories: Array<Category>,
    presets: Array<Preset>,
    onDataChanged: () => void,
}> = ({
    hass,
    categories,
    presets,
    onDataChanged
}): React.JSX.Element => {
    const [targets, setTargets] = useLocalStorage<HaTargetSelectorValue>("scene_presets_apply_page_targets", {});

    const [shuffle, setShuffle] = useLocalStorage<boolean>("scene_presets_apply_page_shuffle", DEFAULT_TUNABLE_SETTINGS.shuffle);
    const [smartShuffle, setSmartShuffle] = useLocalStorage<boolean>("scene_presets_apply_page_smart_shuffle", DEFAULT_TUNABLE_SETTINGS.smartShuffle);
    const [customBrightness, setCustomBrightness] = useLocalStorage<boolean>("scene_presets_apply_page_custom_brightness", DEFAULT_TUNABLE_SETTINGS.customBrightness);
    const [customBrightnessValue, setCustomBrightnessValue] = useLocalStorage<number>("scene_presets_apply_page_custom_brightness_value", DEFAULT_TUNABLE_SETTINGS.customBrightnessValue);
    const [customTransition, setCustomTransition] = useLocalStorage<boolean>("scene_presets_apply_page_custom_transition", DEFAULT_TUNABLE_SETTINGS.customTransition);
    const [customTransitionValue, setCustomTransitionValue] = useLocalStorage<number>("scene_presets_apply_page_custom_transition_value", DEFAULT_TUNABLE_SETTINGS.customTransitionValue);
    const [customEffect, setCustomEffect] = useLocalStorage<boolean>("scene_presets_apply_page_custom_effect", DEFAULT_TUNABLE_SETTINGS.customEffect);
    const [effectValue, setEffectValue] = useLocalStorage<string>("scene_presets_apply_page_effect_value", DEFAULT_TUNABLE_SETTINGS.effectValue);

    const [dynamic, setDynamic] = useLocalStorage<boolean>("scene_presets_apply_page_dynamic", DEFAULT_TUNABLE_SETTINGS.dynamic);
    const [dynamicTransitionValue, setDynamicTransitionValue] = useLocalStorage<number>("scene_presets_apply_page_dynamic_transition_value", DEFAULT_TUNABLE_SETTINGS.dynamicTransitionValue);
    const [dynamicIntervalValue, setDynamicIntervalValue] = useLocalStorage<number>("scene_presets_apply_page_dynamic_interval_value", DEFAULT_TUNABLE_SETTINGS.dynamicIntervalValue);

    const [lastDynamicSceneRefresh, setLastDynamicSceneRefresh] = useState(0);

    const [dynamicScenes, setDynamicScenes] = useState<any>({});
    const dynamicSceneIds = useMemo(() => Object.keys(dynamicScenes), [dynamicScenes]);

    const [applying, setApplying] = useState<boolean>(false);
    const [statusMessage, setStatusMessage] = useState<string>("");
    const [statusIsError, setStatusIsError] = useState<boolean>(false);
    const [presetSearch, setPresetSearch] = useState<string>("");

    const [distribution, setDistribution] = useLocalStorage<string>("scene_presets_apply_page_distribution", "sequence");
    const [transitionStyle, setTransitionStyle] = useLocalStorage<string>("scene_presets_apply_page_transition_style", "fade");
    const [effectPresets, setEffectPresets] = useState<Array<Preset>>([]);
    const [editorOpen, setEditorOpen] = useState<boolean>(false);


    const [favoritePresets, setFavoritePresets] = useLocalStorage<Array<string>>("scene_presets_apply_page_favorite_presets", []);

    const availableEffects = React.useMemo(() => {
        const entityIds = targets?.entity_id;
        const ids = Array.isArray(entityIds) ? entityIds : (entityIds ? [entityIds] : []);
        const effects = new Set<string>();

        ids.forEach((entityId) => {
            const effectList = hass?.states?.[entityId]?.attributes?.effect_list;
            if (Array.isArray(effectList)) {
                effectList.forEach((effect) => effects.add(effect));
            }
        });

        return Array.from(effects).sort();
    }, [hass, targets]);

    const selectedEntityIds = React.useMemo(() => {
        const entityIds = targets?.entity_id;
        return Array.isArray(entityIds) ? entityIds : (entityIds ? [entityIds] : []);
    }, [targets]);

    const localize = React.useCallback(
        (key: string, fallback: string) => hass?.localize?.(`component.scene_presets.${key}`) || fallback,
        [hass]
    );

    const hasTargets = React.useMemo(() => {
        const current = targets || {};
        const values = [current.entity_id, current.device_id, current.area_id, current.floor_id, current.label_id];
        return values.some((value) => (Array.isArray(value) ? value.length > 0 : Boolean(value)));
    }, [targets]);

    useEffect(() => {
        if (!hasTargets) {
            setEffectPresets([]);
            return;
        }

        hass.callWS({type: "scene_presets/get_effect_presets", targets: targets})
            .then((result) => setEffectPresets(result?.presets || []))
            .catch(() => setEffectPresets([]));
    }, [hass, hasTargets, targets]);

    const targetStates = React.useMemo(() => {
        const entityIds = targets?.entity_id;
        const ids = Array.isArray(entityIds) ? entityIds : (entityIds ? [entityIds] : []);
        return ids.map((entityId) => ({
            entityId,
            state: hass?.states?.[entityId]?.state ?? "unknown"
        }));
    }, [hass, targets]);

    const serverSyncHydrated = useRef(false);
    const [serverSync, setServerSync] = useState(false);

    useEffect(() => {
        let cancelled = false;

        hass.callWS({type: "scene_presets/get_config"})
            .then((config) => {
                if (cancelled || !config?.enable_server_sync) {
                    return null;
                }
                setServerSync(true);
                return hass.callWS({type: "scene_presets/get_prefs"});
            })
            .then((prefs) => {
                if (cancelled || !prefs) {
                    return;
                }
                setFavoritePresets(prefs.favorites || []);
                setTargets(prefs.targets || {});
                const tunables = prefs.tunables || {};
                if (typeof tunables.shuffle === "boolean") setShuffle(tunables.shuffle);
                if (typeof tunables.smartShuffle === "boolean") setSmartShuffle(tunables.smartShuffle);
                if (typeof tunables.customBrightness === "boolean") setCustomBrightness(tunables.customBrightness);
                if (typeof tunables.customBrightnessValue === "number") setCustomBrightnessValue(tunables.customBrightnessValue);
                if (typeof tunables.customTransition === "boolean") setCustomTransition(tunables.customTransition);
                if (typeof tunables.customTransitionValue === "number") setCustomTransitionValue(tunables.customTransitionValue);
                if (typeof tunables.customEffect === "boolean") setCustomEffect(tunables.customEffect);
                if (typeof tunables.effectValue === "string") setEffectValue(tunables.effectValue);
                if (typeof tunables.dynamic === "boolean") setDynamic(tunables.dynamic);
                if (typeof tunables.dynamicTransitionValue === "number") setDynamicTransitionValue(tunables.dynamicTransitionValue);
                if (typeof tunables.dynamicIntervalValue === "number") setDynamicIntervalValue(tunables.dynamicIntervalValue);
                if (typeof tunables.distribution === "string") setDistribution(tunables.distribution);
                if (typeof tunables.transitionStyle === "string") setTransitionStyle(tunables.transitionStyle);
                serverSyncHydrated.current = true;
            })
            .catch((error) => {
                setServerSync(false);
                setStatusMessage(error?.message || localize("status.sync_unavailable", "Server sync unavailable; using local storage."));
                setStatusIsError(false);
            });

        return () => {
            cancelled = true;
        };
    }, [hass]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => {
        if (!serverSync || !serverSyncHydrated.current) {
            return;
        }

        const handle = setTimeout(() => {
            hass.callWS({
                type: "scene_presets/set_prefs",
                favorites: favoritePresets,
                targets: targets,
                tunables: {
                    shuffle, smartShuffle,
                    customBrightness, customBrightnessValue,
                    customTransition, customTransitionValue,
                    customEffect, effectValue,
                    dynamic, dynamicTransitionValue, dynamicIntervalValue,
                    distribution, transitionStyle
                }
            }).catch((error) => {
                setStatusMessage(error?.message || localize("status.sync_failed", "Failed to sync preferences."));
                setStatusIsError(true);
            });
        }, 500);

        return () => clearTimeout(handle);
    }, [
        serverSync,
        favoritePresets, targets, shuffle, smartShuffle,
        customBrightness, customBrightnessValue,
        customTransition, customTransitionValue,
        customEffect, effectValue,
        dynamic, dynamicTransitionValue, dynamicIntervalValue,
        distribution, transitionStyle,
        hass
    ]);

    useEffect(() => {
        const existing = getLastStorageError();
        if (existing) {
            setStatusMessage(existing.message);
            setStatusIsError(true);
        }

        const onStorageError = (event: Event) => {
            const detail = (event as CustomEvent).detail;
            setStatusMessage(detail?.message || "Browser storage is unavailable.");
            setStatusIsError(true);
        };

        window.addEventListener(STORAGE_ERROR_EVENT, onStorageError);
        return () => window.removeEventListener(STORAGE_ERROR_EVENT, onStorageError);
    }, []);

    const [automationDialogOpen, setAutomationDialogOpen] = useState<boolean>(false);
    const [lastActionPayload, setLastActionPayload] = useState<any>({});
    const [prettyLastActionPayload, setPrettyLastActionPayload] = useState<string>("");

    const fetchActiveDynamicScenes = React.useCallback(() => {
        hass.callWS({
            type: "scene_presets/get_dynamic_scenes",
        }).then(result => {
            const scenes: any = {};

            result?.dynamic_scenes?.forEach(s => {
                scenes[s.id] = {
                    preset_id: s.parameters.preset_id,
                    interval: s.interval,
                    transition: s.parameters.transition
                };
            });

            setDynamicScenes(scenes);
        }).catch((error) => {
            setStatusMessage(error?.message || "Failed to load dynamic scenes.");
            setStatusIsError(true);
        }).finally(() => {
            setLastDynamicSceneRefresh(Date.now());
        });
    }, [
        hass,
        setLastDynamicSceneRefresh
    ]);

    const handlePresetTap = React.useCallback(
        (id) => {
            if (applying) {
                return;
            }

            if (!hasTargets) {
                setStatusMessage(localize("status.no_targets", "Select at least one target before applying a preset."));
                setStatusIsError(true);
                return;
            }

            let payload: any = {
                preset_id: id,
                targets: targets,

                brightness: customBrightness ? customBrightnessValue : undefined,
                effect: customEffect && effectValue ? effectValue : undefined,
            };

            if (distribution && distribution !== "sequence") {
                payload.distribution = distribution;
            }
            if (transitionStyle && transitionStyle !== "fade") {
                payload.transition_style = transitionStyle;
            }
            let service: string;

            if (dynamic) {
                payload = {
                    ...payload,
                    transition: dynamicTransitionValue,
                    interval: dynamicIntervalValue
                };

                service = "start_dynamic_scene";
            } else {
                payload = {
                    ...payload,
                    shuffle: shuffle,
                    smart_shuffle: smartShuffle,
                    transition: customTransition ? customTransitionValue : undefined,
                };

                service = "apply_preset";
            }

            setLastActionPayload({
                service: `scene_presets.${service}`,
                data: payload
            });

            setApplying(true);
            setStatusMessage("");

            const wantsResponse = service === "start_dynamic_scene";

            hass.callService(
                "scene_presets",
                service,
                payload,
                undefined,
                true,
                wantsResponse
            ).then((response) => {
                const stopped = wantsResponse ? (response?.stopped ?? 0) : 0;
                const conflictNote = stopped > 0
                    ? " " + localize("status.dynamic_conflict", "Overlapping dynamic scenes were stopped.")
                    : "";
                setStatusMessage(localize("status.applied", "Preset applied.") + conflictNote);
                setStatusIsError(false);
            }).catch((error) => {
                setStatusMessage(error?.message || localize("status.failed", "Failed to apply the preset."));
                setStatusIsError(true);
            }).finally(() => {
                setApplying(false);
                fetchActiveDynamicScenes();
            });
        },
        [
            hass, setLastActionPayload,
            targets, shuffle, smartShuffle,
            customBrightness, customBrightnessValue,
            customTransition, customTransitionValue,
            customEffect, effectValue,

            dynamic, dynamicIntervalValue, dynamicTransitionValue,
            hasTargets, localize, applying,
            distribution, transitionStyle,
            fetchActiveDynamicScenes
        ]
    );

    const handleEffectTap = React.useCallback(
        (preset: Preset) => {
            if (!hasTargets) {
                setStatusMessage(localize("status.no_targets", "Select at least one target before applying a preset."));
                setStatusIsError(true);
                return;
            }

            setApplying(true);
            setStatusMessage("");

            hass.callService("scene_presets", "apply_effect", {
                targets: targets,
                effect: preset.effect,
                brightness: customBrightness ? customBrightnessValue : undefined,
            }).then(() => {
                setStatusMessage(localize("status.applied", "Preset applied."));
                setStatusIsError(false);
            }).catch((error) => {
                setStatusMessage(error?.message || localize("status.failed", "Failed to apply the preset."));
                setStatusIsError(true);
            }).finally(() => {
                setApplying(false);
            });
        },
        [hass, targets, hasTargets, customBrightness, customBrightnessValue, localize]
    );

    const handleDeletePreset = React.useCallback(
        (id: string) => {
            if (!window.confirm("Delete this preset?")) {
                return;
            }

            hass.callWS({type: "scene_presets/delete_preset", preset_id: id})
                .then(() => {
                    setStatusMessage(localize("status.deleted", "Preset deleted."));
                    setStatusIsError(false);
                    onDataChanged();
                })
                .catch((error) => {
                    setStatusMessage(error?.message || localize("status.failed", "Failed to apply the preset."));
                    setStatusIsError(true);
                });
        },
        [hass, localize, onDataChanged]
    );

    const handleDynamicSceneTap = React.useCallback(
        (id: string) => {
            hass.callService(
                "scene_presets",
                "stop_dynamic_scene",
                {id: id}
            ).finally(() => {
                fetchActiveDynamicScenes();
            });
        },
        [
            hass, fetchActiveDynamicScenes
        ]
    );

    const presetsByCategories = React.useMemo(() => {
        const out = {};
        const query = presetSearch.trim().toLowerCase();

        categories.forEach(category => {
            out[category.id] = presets.filter(p =>
                p.categoryId === category.id &&
                (!query || p.name.toLowerCase().includes(query))
            );
        });

        return out;
    }, [categories, presets, presetSearch]);


    const tiles = React.useMemo(() => {
        const allTiles: {[key: string] : React.JSX.Element} = {};
        const favoriteTiles: Array<string> = [];

        presets.forEach((preset, i) => {
            const isFav = favoritePresets.includes(preset.id);

            allTiles[preset.id] = <PresetTile
                id={preset.id}
                name={preset.name}
                imgSrc={presetImageUrl(preset)}
                colors={preset.lights}
                onClick={(id) => {
                    handlePresetTap(id);
                }}
                isFav={isFav}
                onFavClick={() => {
                    if (!favoritePresets.includes(preset.id)) {
                        setFavoritePresets([...favoritePresets, preset.id]);
                    } else {
                        setFavoritePresets(favoritePresets.filter(e => e !== preset.id));
                    }
                }}
                onDelete={preset.custom ? handleDeletePreset : undefined}
            />;

            if (isFav) {
                favoriteTiles.push(preset.id);
            }
        });

        return {
            all: allTiles,
            favoriteIds: favoriteTiles,
        };
    }, [presets, favoritePresets, handlePresetTap, setFavoritePresets, handleDeletePreset]);

    const presetMap = useMemo(() => {
        const _presetMap = {};

        presets.forEach(p => {
            _presetMap[p.id] = p;
        });

        return _presetMap;
    }, [presets]);

    /**
     * This is a hack that works around the fact that for whatever reason, componentWillUnmount never fires.
     * Possibly because using react in this setup is cursed
     */
    useEffect(() => {
        if (Date.now() - lastDynamicSceneRefresh >= DYNAMIC_SCENE_REFRESH_INTERVAL) {
            fetchActiveDynamicScenes();
        }
    }, [hass, fetchActiveDynamicScenes]); // eslint-disable-line react-hooks/exhaustive-deps 

    return (
        <div
            style={{
                padding: "1rem",
                userSelect: "none"
            }}
        >
            <div
                style={{
                    maxWidth: "1080px", //same as hass
                    marginLeft: "auto",
                    marginRight: "auto"
                }}
            >
                <ha-card>
                    <div
                        style={{
                            padding: "1rem"
                        }}
                    >
                        <span style={{
                            fontWeight: "bolder",
                            fontSize: "1.25rem"
                        }}>
                            <div style={{display: "flex"}}>
                                {localize("ui.targets", "Targets")}
                                <div
                                    style={{
                                        marginTop: "-0.4rem",
                                        marginLeft: "0.5rem"
                                    }}>
                                    <HaIconButton
                                        icon={"mdi:broom"}
                                        onClick={() => setTargets({})}

                                        size={28}
                                        iconSize={24}
                                    />
                                </div>
                                <div
                                    style={{
                                        position: "absolute",
                                        top: "0.5rem",
                                        right: "1rem"
                                    }}>
                                    <HaIconButton
                                        icon={"mdi:robot"}
                                        onClick={
                                            () => {
                                                setPrettyLastActionPayload(JSON.stringify(lastActionPayload, null, 2));
                                                setAutomationDialogOpen(true);
                                            }
                                        }
                                        size={28}
                                        iconSize={24}
                                    />
                                </div>
                            </div>
                        </span>
                        <div
                            style={{
                                marginTop: "1rem"
                            }}
                        >
                            <HaTargetSelector
                                hass={hass}
                                selector={{
                                    "target": {
                                        "entity": {
                                            "domain": [
                                                "light",
                                                "group"
                                            ]
                                        }
                                    }
                                }}
                                value={targets}
                                onValueChanged={(value) => {
                                    setTargets(value);
                                }}
                            />
                        </div>
                        {
                            targetStates.length > 0 &&
                            <div
                                style={{
                                    marginTop: "0.5rem",
                                    fontFamily: "monospace",
                                    fontSize: "0.8rem"
                                }}
                            >
                                {
                                    targetStates.map(({entityId, state}) => (
                                        <span key={entityId} style={{marginRight: "0.75rem"}}>
                                            {entityId}: {state}
                                        </span>
                                    ))
                                }
                            </div>
                        }
                        <div
                            style={{
                                fontWeight: "bolder",
                                marginTop: "1rem",
                                marginBottom: "1rem",
                                fontSize: "1.25rem"
                            }}
                        >
                            <div style={{display: "flex"}}>
                                {localize("ui.tunables", "Tunables")}
                                <div
                                    style={{
                                        marginTop: "-0.4rem",
                                        marginLeft: "0.5rem"
                                    }}>
                                    <HaIconButton
                                        icon={"mdi:restore"}
                                        onClick={() => {
                                            setShuffle(DEFAULT_TUNABLE_SETTINGS.shuffle);
                                            setSmartShuffle(DEFAULT_TUNABLE_SETTINGS.smartShuffle);
                                            setCustomBrightness(DEFAULT_TUNABLE_SETTINGS.customBrightness);
                                            setCustomBrightnessValue(DEFAULT_TUNABLE_SETTINGS.customBrightnessValue);
                                            setCustomTransition(DEFAULT_TUNABLE_SETTINGS.customTransition);
                                            setCustomTransitionValue(DEFAULT_TUNABLE_SETTINGS.customTransitionValue);
                                            setCustomEffect(DEFAULT_TUNABLE_SETTINGS.customEffect);
                                            setEffectValue(DEFAULT_TUNABLE_SETTINGS.effectValue);

                                            setDynamic(DEFAULT_TUNABLE_SETTINGS.dynamic);
                                            setDynamicTransitionValue(DEFAULT_TUNABLE_SETTINGS.dynamicTransitionValue);
                                            setDynamicIntervalValue(DEFAULT_TUNABLE_SETTINGS.dynamicIntervalValue);
                                            setDistribution("sequence");
                                            setTransitionStyle("fade");
                                        }}

                                        size={28}
                                        iconSize={24}
                                    />
                                </div>
                            </div>
                        </div>
                        <label
                            style={{
                                lineHeight: "3rem"
                            }}
                        >
                            <Switch
                                label={localize("ui.dynamic", "Dynamic")}
                                value={dynamic}
                                setValue={(v) => setDynamic(v)}
                            />
                        </label>
                        <br/>
                        {
                            !dynamic &&
                            <>
                                <Switch
                                    label={localize("ui.shuffle", "Shuffle Colors")}
                                    value={shuffle}
                                    setValue={(v) => setShuffle(v)}
                                />
                                <br/>

                                {
                                    shuffle &&
                                    <>
                                        <div
                                            style={{marginLeft: "1rem"}}
                                        >
                                            <Switch
                                                label={localize("ui.smart_shuffle", "Smart Shuffle")}
                                                value={smartShuffle}
                                                setValue={(v) => setSmartShuffle(v)}
                                            />
                                        </div>
                                    </>
                                }
                            </>
                        }
                        {
                            dynamic &&
                            <>
                                <NumberSelector
                                    label={localize("ui.interval", "Interval")}
                                    value={dynamicIntervalValue}
                                    setValue={(v) => setDynamicIntervalValue(v)}
                                    minValue={1}
                                    maxValue={300}
                                    hass={hass}
                                    extraSelectorProps={{"unit_of_measurement": "seconds"}}
                                />

                                <NumberSelector
                                    label={localize("ui.transition", "Transition")}
                                    value={dynamicTransitionValue}
                                    setValue={(v) => setDynamicTransitionValue(v)}
                                    minValue={0}
                                    maxValue={300}
                                    hass={hass}
                                    extraSelectorProps={{"unit_of_measurement": "seconds"}}
                                />
                            </>
                        }



                        <OptionalNumberSelector
                            label={localize("ui.custom_brightness", "Custom Brightness")}
                            enabled={customBrightness}
                            setEnabled={(v) => setCustomBrightness(v)}
                            value={customBrightnessValue}
                            setValue={(v) => setCustomBrightnessValue(v)}
                            minValue={0}
                            maxValue={255}
                            hass={hass}
                        />
                        {
                            !customBrightness && !dynamic &&
                            <br/>
                        }

                        {
                            !dynamic &&
                            <OptionalNumberSelector
                                label={localize("ui.custom_transition", "Custom Transition")}
                                enabled={customTransition}
                                setEnabled={(v) => setCustomTransition(v)}
                                value={customTransitionValue}
                                setValue={(v) => setCustomTransitionValue(v)}
                                minValue={0}
                                maxValue={300}
                                hass={hass}
                                extraSelectorProps={{"unit_of_measurement": "seconds"}}
                            />
                        }

                        {
                            availableEffects.length > 0 &&
                            <OptionalSelect
                                label={localize("ui.custom_effect", "Custom Effect")}
                                enabled={customEffect}
                                setEnabled={(v) => setCustomEffect(v)}
                                value={effectValue}
                                setValue={(v) => setEffectValue(v)}
                                options={availableEffects}
                                hass={hass}
                            />
                        }

                        <LabeledSelect
                            label={localize("ui.distribution", "Distribution")}
                            value={distribution}
                            setValue={(v) => setDistribution(v)}
                            options={["sequence", "balanced", "random"]}
                            hass={hass}
                        />

                        <LabeledSelect
                            label={localize("ui.transition_style", "Transition style")}
                            value={transitionStyle}
                            setValue={(v) => setTransitionStyle(v)}
                            options={["fade", "instant", "ease_in", "ease_out", "ease_in_out"]}
                            hass={hass}
                        />
                    </div>
                </ha-card>

                {
                    (applying || statusMessage) &&
                    <div
                        role={"status"}
                        aria-live={"polite"}
                        style={{
                            padding: "0.75rem 1rem",
                            marginTop: "1rem",
                            borderRadius: "8px",
                            backgroundColor: statusIsError ? "#7f1d1d" : "#14532d",
                            color: "#ffffff",
                            fontFamily: "sans-serif"
                        }}
                    >
                        {applying ? localize("status.applying", "Applying…") : statusMessage}
                    </div>
                }

                <div
                    style={{
                        marginTop: "1rem",
                        maxWidth: "540px"
                    }}
                >
                    <input
                        type={"search"}
                        value={presetSearch}
                        placeholder={localize("search.placeholder", "Search presets")}
                        aria-label={localize("search.placeholder", "Search presets")}
                        onChange={(event) => setPresetSearch(event.target.value)}
                        style={{
                            width: "100%",
                            boxSizing: "border-box",
                            padding: "0.75rem",
                            borderRadius: "8px",
                            border: "1px solid var(--divider-color, #cccccc)",
                            backgroundColor: "var(--card-background-color, transparent)",
                            color: "var(--primary-text-color, inherit)",
                            fontFamily: "sans-serif"
                        }}
                    />
                </div>

                <div
                    style={{
                        marginTop: "0.75rem"
                    }}
                >
                    <HaButton
                        label={localize("ui.create_preset", "Create preset")}
                        onClick={() => setEditorOpen(true)}
                    />
                </div>

                {
                    dynamicSceneIds.length > 0 &&
                    <div
                        key={"category_dynamic_scenes"}
                    >
                        <h3
                            style={{
                                fontFamily: "sans-serif"
                            }}
                        >
                            {localize("ui.dynamic_scenes", "Dynamic scenes")}
                        </h3>
                        <div
                            style={{
                                display: "flex",
                                flexWrap: "wrap",
                                justifyContent: "center"
                            }}
                        >
                            {
                                dynamicSceneIds.map(id => {
                                    const preset = presetMap[dynamicScenes[id]?.preset_id];

                                    const name = preset?.name ?? "Unknown Preset";
                                    const imgSrc = preset ? presetImageUrl(preset) : undefined;

                                    return <DynamicSceneTile
                                        key={"active_dynamic_scene_" + id}
                                        id={id}
                                        name={name}
                                        interval={dynamicScenes[id]?.interval ?? -1}
                                        transition={dynamicScenes[id]?.transition ?? -1}
                                        imgSrc={imgSrc}
                                        onClick={(id) => {
                                            handleDynamicSceneTap(id);
                                        }}
                                    />;
                                })
                            }
                        </div>
                    </div>
                }

                {
                    tiles.favoriteIds.length > 0 &&
                    <div
                        key={"category_favorites"}
                    >
                        <h3
                            style={{
                                fontFamily: "sans-serif"
                            }}
                        >
                            {localize("ui.favorites", "Favorites")}
                        </h3>
                        <div
                            style={{
                                display: "flex",
                                flexWrap: "wrap",
                                justifyContent: "center"
                            }}
                        >
                            {
                                tiles.favoriteIds.map(id => {
                                    return <React.Fragment key={"favorite_" + id}>
                                        {tiles.all[id]}
                                    </React.Fragment>;
                                })
                            }
                        </div>
                    </div>

                }

                {
                    categories.map(({name, id}) => {
                        return (
                            <div
                                key={"category_" + name}
                            >
                                <h3
                                    style={{
                                        fontFamily: "sans-serif"
                                    }}
                                >
                                    {name}
                                </h3>
                                <div
                                    style={{
                                        display: "flex",
                                        flexWrap: "wrap",
                                        justifyContent: "center"
                                    }}
                                >
                                    <CategoryTiles
                                        presets={presetsByCategories[id]}
                                        renderTile={(presetId) => tiles.all[presetId]}
                                    />
                                </div>
                            </div>
                        );
                    })
                }

                {
                    effectPresets.length > 0 &&
                    <div key={"category_wled_effects"}>
                        <h3
                            style={{
                                fontFamily: "sans-serif"
                            }}
                        >
                            {localize("ui.wled_effects", "WLED Effects")}
                        </h3>
                        <div
                            style={{
                                display: "flex",
                                flexWrap: "wrap",
                                justifyContent: "center"
                            }}
                        >
                            {
                                effectPresets.map((preset) => (
                                    <PresetTile
                                        key={"effect_" + preset.id}
                                        id={preset.id}
                                        name={preset.name}
                                        colors={preset.lights}
                                        onClick={() => handleEffectTap(preset)}
                                    />
                                ))
                            }
                        </div>
                    </div>
                }

                {
                    editorOpen &&
                    <PresetEditor
                        hass={hass}
                        categories={categories}
                        availableEffects={availableEffects}
                        onClose={() => setEditorOpen(false)}
                        onSaved={onDataChanged}
                    />
                }

                <HaDialog
                    open={automationDialogOpen}
                    onClose={() => {
                        setAutomationDialogOpen(false);
                    }}
                    heading={localize("ui.last_action", "Last action payload")}
                >
                    <div>
                        Here you can see the payload used by your last action that applied a preset or started a dynamic scene.
                        This can be used in automations, scripts etc.
                    </div>

                    <div style={{padding: "1rem"}}>
                        <pre
                            style={{
                                backgroundColor: "#000000",
                                padding: "1rem",
                                userSelect: "text",
                                color: "#ffffff",
                                fontFamily: "monospace",
                                fontWeight: 200,
                                whiteSpace: "pre-wrap"
                            }}
                        >
                            {prettyLastActionPayload}
                        </pre>
                    </div>

                    <div style={{display: "flex", justifyContent: "flex-end", marginTop: "0.5rem"}}>
                        <HaButton
                            label={"Close"}
                            variant={"secondary"}
                            onClick={() => {
                                setAutomationDialogOpen(false);
                            }}
                        />
                    </div>
                </HaDialog>
            </div>

        </div>
    );
};
