import React, {Component} from "react";

export interface HaSelectorProps {
    hass: any;
    selector: any;
    value: any;
    onValueChanged: (value: any) => void
}

abstract class HaSelector<P> extends Component<P & HaSelectorProps> {
    private elementRef: React.RefObject<HTMLElement | null>;

    constructor(props: P & HaSelectorProps) {
        super(props);

        this.elementRef = React.createRef();
    }

    state = {
        hasNativeHaSelector: typeof customElements !== "undefined" && Boolean(customElements.get("ha-selector"))
    };

    handleValueChanged = (event) => {
        this.props.onValueChanged(event.detail.value);
    };

    handleFallbackChanged = (event) => {
        const numberConfig = this.props.selector?.number;
        this.props.onValueChanged(numberConfig ? Number(event.target.value) : event.target.value);
    };

    componentDidMount() {
        const {hasNativeHaSelector} = this.state;

        if (!hasNativeHaSelector && typeof customElements !== "undefined") {
            customElements.whenDefined("ha-selector")
                .then(() => this.setState({hasNativeHaSelector: true}))
                .catch(() => undefined);
        }

        if (this.elementRef.current) {
            this.elementRef.current.addEventListener("value-changed", this.handleValueChanged);
        }
    }

    componentWillUnmount() {
        if (this.elementRef.current) {
            this.elementRef.current.removeEventListener("value-changed", this.handleValueChanged);
        }
    }

    render() {
        if (!this.state.hasNativeHaSelector) {
            const numberConfig = this.props.selector?.number;

            return (
                <input
                    type={numberConfig ? "number" : "text"}
                    value={this.props.value ?? ""}
                    min={numberConfig?.min}
                    max={numberConfig?.max}
                    onChange={this.handleFallbackChanged}
                />
            );
        }

        return (
            <ha-selector
                ref={this.elementRef}
                hass={this.props.hass}
                selector={this.props.selector}
                value={this.props.value}
            />
        );
    }

}

export default HaSelector;
