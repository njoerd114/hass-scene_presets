import {useState} from "react";

import {reportStorageError} from "./storageErrors";

export const useSessionStorage = <T>(key: string, initialValue: T): [T, (s: T) => void] => {
    const [storedValue, setStoredValue] = useState<T>(() => {
        try {
            const item = window.sessionStorage.getItem(key);
            return item ? JSON.parse(item) : initialValue;
        } catch (error) {
            reportStorageError("session", error);
            return initialValue;
        }
    });

    const setValue = (value: T) => {
        const valueToStore = value instanceof Function ? value(storedValue) : value;
        setStoredValue(valueToStore);
        try {
            window.sessionStorage.setItem(key, JSON.stringify(valueToStore));
        } catch (error) {
            reportStorageError("session", error);
        }
    };

    return [storedValue, setValue];
};
