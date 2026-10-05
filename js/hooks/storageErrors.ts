import {logWarning} from "../log";

export const STORAGE_ERROR_EVENT = "scene-presets-storage-error";

export interface StorageError {
    kind: string;
    message: string;
}

let lastStorageError: StorageError | null = null;

export const getLastStorageError = (): StorageError | null => lastStorageError;

export const reportStorageError = (kind: string, error: unknown) => {
    const message = error instanceof Error ? error.message : String(error);
    lastStorageError = {kind, message};
    logWarning(`failed to access ${kind} storage`, message);

    window.dispatchEvent(new CustomEvent(STORAGE_ERROR_EVENT, {
        detail: {kind, message}
    }));
};
