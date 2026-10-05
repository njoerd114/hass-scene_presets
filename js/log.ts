export const logWarning = (message: string, ...args: Array<unknown>) => {
    console.warn(`Scene presets: ${message}`, ...args);
};

export const logError = (message: string, ...args: Array<unknown>) => {
    console.error(`Scene presets: ${message}`, ...args);
};
