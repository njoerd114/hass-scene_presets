import React, {Component, ReactNode} from "react";

interface HaDialogProps {
    open: boolean;
    onClose: () => void
    heading?: string,
    children?: ReactNode;
}

class HaDialog extends Component<HaDialogProps> {
    private elementRef: React.RefObject<HTMLElement | null>;

    constructor(props: HaDialogProps) {
        super(props);

        this.elementRef = React.createRef();
    }

    handleClosed = () => {
        this.props.onClose();
    };

    componentDidMount() {
        this.applyProperties();
        if (this.elementRef.current) {
            this.elementRef.current.addEventListener("closed", this.handleClosed);
        }
    }

    componentDidUpdate() {
        this.applyProperties();
    }

    componentWillUnmount() {
        if (this.elementRef.current) {
            this.elementRef.current.removeEventListener("closed", this.handleClosed);
        }
    }

    applyProperties() {
        const element: any = this.elementRef.current;
        if (!element) {
            return;
        }

        element.open = this.props.open;
        if (this.props.heading !== undefined) {
            element.headerTitle = this.props.heading;
        }
    }

    render() {
        return (
            <ha-dialog ref={this.elementRef}>
                {this.props.children}
            </ha-dialog>
        );
    }

}

export default HaDialog;
