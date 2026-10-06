import React from "react";
import HaIconButton from "./hass/building_blocks/HaIconButton";
import {xyToCssColor} from "../helpers";

export const PresetTile :React.FunctionComponent<{
    id: string,
    name: string,
    imgSrc?: string
    colors?: Array<{x: number, y: number}>
    onClick?: (name: string) => void

    onFavClick?: (name: string) => void
    isFav?: boolean
    onDelete?: (name: string) => void
    onEdit?: (name: string) => void
}> = ({
    id,
    name,
    imgSrc,
    colors,
    onClick,

    onFavClick,
    isFav,
    onDelete,
    onEdit
}): React.JSX.Element => {
    const preview = colors && colors.length > 0
        ? `linear-gradient(135deg, ${colors.map((color) => xyToCssColor(color.x, color.y)).join(", ")})`
        : undefined;
    // These two variables are _somehow_ required because without the change in key, the icon won't change even though we get rerendered ??
    const favedIcon = <HaIconButton
        key={"id_fav"}
        icon={"mdi:star"}
        onClick={() => {
            onFavClick?.(id);
        }}

        size={28}
        iconSize={24}
    />;
    const unFavedIcon = <HaIconButton
        key={"id_unfav"}
        icon={"mdi:star-outline"}
        onClick={() => {
            onFavClick?.(id);
        }}

        size={28}
        iconSize={24}
    />;

    return (
        <div
            className={"tile"}
            role={"button"}
            tabIndex={0}
            aria-label={name}
            onClick={() => {
                onClick?.(id);
            }}
            onKeyDown={(event) => {
                if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    onClick?.(id);
                }
            }}
        >
            {
                onFavClick &&
                <div
                    className={"tile-top-icon-container"}
                >
                    {
                        isFav ? favedIcon : unFavedIcon
                    }
                </div>
            }

            {
                onDelete &&
                <div
                    className={"tile-top-icon-container"}
                    style={{left: "10px", right: "auto"}}
                    onClick={(event) => {
                        event.stopPropagation();
                    }}
                >
                    <HaIconButton
                        icon={"mdi:trash-can-outline"}
                        onClick={() => {
                            onDelete(id);
                        }}

                        size={28}
                        iconSize={24}
                    />
                </div>
            }

            {
                onEdit &&
                <div
                    className={"tile-top-icon-container"}
                    style={{left: "44px", right: "auto"}}
                    onClick={(event) => {
                        event.stopPropagation();
                    }}
                >
                    <HaIconButton
                        icon={"mdi:pencil-outline"}
                        onClick={() => {
                            onEdit(id);
                        }}

                        size={28}
                        iconSize={24}
                    />
                </div>
            }

            <div
                className={"tile-content"}
            >
                {
                    imgSrc ?

                        <img
                            src={imgSrc}
                            alt={name}
                            className={"tile-bg-img"}
                        />
                        :
                        <div
                            className={"tile-bg-no-img"}
                            style={preview ? {background: preview, backgroundSize: "100% 100%"} : undefined}
                        >
                        </div>

                }
                <div
                    className={"tile-text-bg"}
                ></div>
                <p
                    className={"tile-text"}
                >
                    {name}
                </p>
            </div>
        </div>
    );
};
