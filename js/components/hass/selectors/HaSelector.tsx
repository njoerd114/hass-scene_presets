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

    handleValueChanged = (event: any) => {
        this.props.onValueChanged(event.detail.value);
    };

    handleFallbackChanged = (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
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

        this.applyProperties();
    }

    componentDidUpdate() {
        this.applyProperties();
    }

    componentWillUnmount() {
        if (this.elementRef.current) {
            this.elementRef.current.removeEventListener("value-changed", this.handleValueChanged);
        }
    }

    applyProperties() {
        const element: any = this.elementRef.current;

        if (!element || !this.state.hasNativeHaSelector) {
            return;
        }

        element.hass = this.props.hass;
        element.selector = this.props.selector;
        element.value = this.props.value;

        element.removeEventListener("value-changed", this.handleValueChanged);
        element.addEventListener("value-changed", this.handleValueChanged);
    }

    renderFallback() {
        const selector = this.props.selector ?? {};
        const value = this.props.value ?? "";

        if (selector.number) {
            return (
                <input
                    type={"number"}
                    value={value}
                    min={selector.number.min}
                    max={selector.number.max}
                    step={selector.number.step}
                    onChange={this.handleFallbackChanged}
                />
            );
        }

        if (selector.select?.options) {
            return (
                <select value={value} onChange={this.handleFallbackChanged}>
                    {
                        selector.select.options.map((option: any) => {
                            const optionValue = typeof option === "object" ? option.value : option;
                            const optionLabel = typeof option === "object" ? option.label : option;
                            return <option key={optionValue} value={optionValue}>{optionLabel}</option>;
                        })
                    }
                </select>
            );
        }

        return (
            <input
                type={"text"}
                value={value}
                onChange={this.handleFallbackChanged}
            />
        );
    }

    render() {
        if (!this.state.hasNativeHaSelector) {
            return this.renderFallback();
        }

        return (
            <ha-selector ref={this.elementRef} />
        );
    }

}

export default HaSelector;
