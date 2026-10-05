import React from "react";

import {useWindowedList} from "../hooks/useWindowedList";

export const CategoryTiles :React.FunctionComponent<{
    presets: Array<{id: string}>,
    renderTile: (id: string) => React.ReactNode,
    pageSize?: number
}> = ({
    presets,
    renderTile,
    pageSize = 30
}): React.JSX.Element => {
    const [visible, showMore, hasMore] = useWindowedList(presets, pageSize);

    return (
        <>
            {
                visible.map((preset) => (
                    <React.Fragment key={"windowed_" + preset.id}>
                        {renderTile(preset.id)}
                    </React.Fragment>
                ))
            }
            {
                hasMore &&
                <button
                    type={"button"}
                    onClick={showMore}
                    aria-label={"Show more presets"}
                    style={{
                        margin: "10px",
                        padding: "0.75rem 1rem",
                        borderRadius: "15px",
                        border: "none",
                        cursor: "pointer",
                        fontFamily: "sans-serif"
                    }}
                >
                    Show more ({presets.length - visible.length} remaining)
                </button>
            }
        </>
    );
};
