import { useEffect } from "react";

export function handleClickOutside(ref, callback) {
    useEffect(() => {
        const handleClick = e => {
            if (ref.current && !ref.current.contains(e.target)) {
                callback();
            }
        };

        document.addEventListener('click', handleClick);

        return () => {
            document.removeEventListener('click', handleClick);
        };
    }, [ref, callback]);
}