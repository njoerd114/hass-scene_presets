
// Loads in ha-config-dashboard which is used to copy styling
// Also provides ha-settings-row
import {logWarning} from "./log";

export const loadConfigDashboard = async () => {
    try {
        await customElements.whenDefined("partial-panel-resolver");
        const ppResolver = document.createElement("partial-panel-resolver");

        const getRoutes = (ppResolver as any)._getRoutes ?? (ppResolver as any).getRoutes;

        if (typeof getRoutes !== "function") {
            logWarning("Home Assistant routing tree is unavailable");
            return;
        }

        const routes = getRoutes([
            {
                component_name: "config",
                url_path: "a",
            },
            {
                component_name: "developer-tools",
                url_path: "b",
            },
        ]);
        await routes?.routes?.a?.load?.();
        await customElements.whenDefined("ha-panel-config");
        const configRouter: any = document.createElement("ha-panel-config");
        await configRouter?.routerOptions?.routes?.dashboard?.load?.(); // Load ha-config-dashboard
        await configRouter?.routerOptions?.routes?.general?.load?.(); // Load ha-settings-row
        await configRouter?.routerOptions?.routes?.entities?.load?.(); // Load ha-data-table
        await customElements.whenDefined("ha-config-dashboard");


        // For the selectors

        //  Before 2026.2, the devtools are their own route
        const devToolsRoute = await routes?.routes?.b?.load?.();
        // After HA 2026.2, the devtools are a sub-route of the config
        const devToolsConfigSubRoute = await configRouter?.routerOptions?.routes?.["developer-tools"]?.load?.();
        // After HA 2026.8, devtools have been renamed to tools, because dev is a scary word, apparently.
        const devlessDevToolsConfigSubRoute = await configRouter?.routerOptions?.routes?.["tools"]?.load?.();

        if (devlessDevToolsConfigSubRoute) {
            await customElements.whenDefined("ha-panel-tools");
            const toolsRouter: any = document.createElement("tools-router");

            await toolsRouter?.routerOptions?.routes?.action?.load?.();

        } else if (devToolsRoute || devToolsConfigSubRoute) {
            await customElements.whenDefined("ha-panel-developer-tools");
            const devToolsRouter: any = document.createElement("developer-tools-router");

            await devToolsRouter?.routerOptions?.routes?.service?.load?.(); // Home assistant before 2024.8 => service
            await devToolsRouter?.routerOptions?.routes?.action?.load?.(); // Home assistant after 2024.8 => action
        } else {
            logWarning("Home Assistant devtools could not be found in the routing tree");
        }
    } catch (error) {
        logWarning("failed to preload Home Assistant dependencies", error);
    }
};

const _gamma = (channel: number): number => {
    const clamped = Math.max(0, Math.min(1, channel));
    const encoded = clamped <= 0.0031308 ? 12.92 * clamped : 1.055 * Math.pow(clamped, 1 / 2.4) - 0.055;
    return Math.round(255 * Math.max(0, Math.min(1, encoded)));
};

export const xyToCssColor = (x: number, y: number): string => {
    const z = 1 - x - y;
    const red = x * 3.2406 - y * 1.5372 - z * 0.4986;
    const green = -x * 0.9689 + y * 1.8758 + z * 0.0415;
    const blue = x * 0.0557 - y * 0.2040 + z * 1.0570;

    return `rgb(${_gamma(red)}, ${_gamma(green)}, ${_gamma(blue)})`;
};

export const presetImageUrl = (preset: {img?: string; custom?: boolean}): string | undefined => {
    if (!preset?.img) {
        return undefined;
    }

    const base = preset.custom ? "/assets/scene_presets/custom/" : "/assets/scene_presets/";
    return base + preset.img;
};
