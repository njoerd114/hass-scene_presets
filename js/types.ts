
export type Category = {
    id: string,
    name: string
}

export type Preset = {
    id: string,
    categoryId: string,
    name: string,
    img: string,
    bri: number,
    effect?: string,
    kelvin?: number,
    white?: number,
    custom?: boolean,
    lights: Array<{x: number, y: number}>
}
