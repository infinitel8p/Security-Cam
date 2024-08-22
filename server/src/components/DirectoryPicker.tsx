"use client";
import React, { useState, useEffect } from 'react';

type DirectoryList = {
    name: string;
    path: string;
}[];

const DirectoryPicker = ({ onDirectorySelect } : {onDirectorySelect: any}) => {
    const [directories, setDirectories] = useState<DirectoryList>([]);
    const [currentPath, setCurrentPath] = useState<string>('/');
    const [error, setError] = useState<string>('');
    const [directoriesUrl, setDirectoriesUrl] = useState<string>('');

    useEffect(() => {
        if (typeof window !== "undefined") {
            setDirectoriesUrl(`${window.location.protocol}//${window.location.hostname}:5005/list_directories`);
        }
    }, []);

    useEffect(() => {
        if (directoriesUrl) {
            fetchDirectories(currentPath);
        }
    }, [directoriesUrl, currentPath]);

    const fetchDirectories = async (path: string) => {
        try {
            const response = await fetch(`${directoriesUrl}?path=${encodeURIComponent(path)}`);
            const data = await response.json();
            if (response.ok) {
                setDirectories(data.directories);
                setCurrentPath(data.current_path);
            } else {
                setError(data.error);
            }
        } catch (error) {
            setError('Failed to fetch directories.');
        }
    };

    const handleDirectoryClick = (path: string) => {
        setCurrentPath(path);
        onDirectorySelect(path);
    };

    return (
        <div>
            <h3>Current Directory: {currentPath}</h3>
            {error && <div style={{ color: 'red' }}>{error}</div>}
            <ul>
                {directories.map((dir) => (
                    <li key={dir.path}>
                        <button className='bg-red-500 m-1' onClick={() => handleDirectoryClick(dir.path)}>
                            {dir.name}
                        </button>
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default DirectoryPicker;
