import HaSelector, {HaSelectorProps} from "./HaSelector";

export interface HaSelectProps extends HaSelectorProps {
    value: string
    onValueChanged: (value: string) => void
}

export class HaSelect extends HaSelector<HaSelectProps> {}
