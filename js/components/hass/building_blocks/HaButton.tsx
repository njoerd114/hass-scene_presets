import React from "react";

export interface HaButtonProps {
    label: string;
    onClick: (event: React.MouseEvent<HTMLButtonElement>) => void;
    variant?: "primary" | "secondary";
    disabled?: boolean;
}

const HaButton :React.FunctionComponent<HaButtonProps> = ({
    label,
    onClick,
    variant = "primary",
    disabled = false
}): React.JSX.Element => {
    const primary = variant === "primary";

    return (
        <button
            type={"button"}
            disabled={disabled}
            onClick={onClick}
            style={{
                padding: "0.6rem 1.1rem",
                borderRadius: "8px",
                border: primary ? "1px solid transparent" : "1px solid var(--divider-color, #cccccc)",
                background: primary ? "var(--primary-color, #03a9f4)" : "transparent",
                color: primary ? "var(--text-primary-color, #ffffff)" : "var(--primary-text-color, inherit)",
                cursor: disabled ? "default" : "pointer",
                fontFamily: "sans-serif",
                fontSize: "0.9rem",
                opacity: disabled ? 0.6 : 1
            }}
        >
            {label}
        </button>
    );
};

export default HaButton;
