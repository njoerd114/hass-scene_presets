import React from "react";

import HaSelector, {HaSelectorProps} from "./HaSelector";

export interface HaTargetSelectorValue {
    entity_id?: string | Array<string>,
    device_id?: string | Array<string>,
    area_id?: string | Array<string>,
    floor_id?: string | Array<string>,
    label_id?: string | Array<string>
}

export interface HaTargetSelectorProps extends HaSelectorProps {
    value: HaTargetSelectorValue
    onValueChanged: (value: HaTargetSelectorValue) => void
}

export class HaTargetSelector extends HaSelector<HaTargetSelectorProps> {
    render(): React.JSX.Element {
        if (this.state.hasNativeHaSelector) {
            return super.render();
        }

        const current = this.props.value?.entity_id;
        const value = Array.isArray(current) ? current.join(", ") : (current || "");

        return (
            <input
                type={"text"}
                value={value}
                placeholder={"light.living_room, light.kitchen"}
                aria-label={"Target light entities"}
                onChange={(event) => {
                    const ids = event.target.value
                        .split(",")
                        .map((entry) => entry.trim())
                        .filter(Boolean);
                    this.props.onValueChanged(ids.length > 0 ? {entity_id: ids} : {});
                }}
            />
        );
    }
}
