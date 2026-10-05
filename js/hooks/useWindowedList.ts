import {useEffect, useState} from "react";

export const useWindowedList = <T,>(items: Array<T>, pageSize: number): [Array<T>, () => void, boolean] => {
    const [limit, setLimit] = useState(pageSize);

    useEffect(() => {
        setLimit(pageSize);
    }, [items, pageSize]);

    const visible = items.slice(0, limit);
    const hasMore = limit < items.length;
    const showMore = () => setLimit((current) => current + pageSize);

    return [visible, showMore, hasMore];
};
