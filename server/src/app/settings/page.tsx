'use client';
import React, { useState, useEffect } from "react";
import DirectoryPicker from "@/components/DirectoryPicker";
import BTDeviceList from "@/components/BTDeviceList";
import WiFiDeviceList from "@/components/WiFiDeviceList";

const Page = () => {

    const [settingsURL, setSettingsURL] = useState<string>('');
    const [selectedDirectory, setSelectedDirectory] = useState('');
    const [settings, setSettings] = useState({
        VideoSaveLocation: "Loading...",
    });

    const handleDirectorySelect = (path: string) => {
        setSelectedDirectory(path);
    };

    // Set the settingsURL when the component mounts
    useEffect(() => {
        if (typeof window !== "undefined") {
            setSettingsURL(`${window.location.protocol}//${window.location.hostname}:5005/settings`);
        }
    }, []);

    // Fetch settings once settingsURL is set
    useEffect(() => {
        const fetchSettingsInfo = async () => {
            if (settingsURL) {
                try {
                    console.log(settingsURL);
                    const response = await fetch(settingsURL);
                    const data = await response.json();
                    setSettings(data);
                } catch (error) {
                    console.error("Error fetching settings info:", error);
                    setSettings({
                        VideoSaveLocation: "Error loading data",
                    });
                }
            }
        };

        fetchSettingsInfo();
    }, [settingsURL]); // Run this effect whenever settingsURL changes

    const handleSaveLocationChange = async () => {
        try {
            const response = await fetch(settingsURL, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ VideoSaveLocation: selectedDirectory }),
            });

            const result = await response.json();
            if (!response.ok) {
                alert(result.message || "Error updating settings");
            } else {
                alert("Settings updated successfully");
                setSettings(prevSettings => ({ ...prevSettings, VideoSaveLocation: selectedDirectory }));
            }
        } catch (error) {
            console.error("Error updating settings:", error);
            alert("Error updating settings");
        }
    };

    return (
        <div className="flex flex-col gap-5 space-y-10 px-10 pt-10">
            <div className="border border-red-500">
                <BTDeviceList />
            </div>
            <div className="border border-red-500">
                <WiFiDeviceList />
            </div>
            <div className="flex w-full border border-red-500">
                <div>Video save location: <span className="text-blue-700">{settings.VideoSaveLocation}</span></div>
                <div className="flex gap-5 ml-5">
                    <div>
                        <h1>Select a new directory to save the videos:</h1>
                        <DirectoryPicker onDirectorySelect={handleDirectorySelect} />
                    </div>
                    <button className="bg-gray-500 border rounded-md p-2 h-10 m-auto" onClick={handleSaveLocationChange}>Update Location</button>
                </div>
            </div>
            <div className="border border-red-500 text-gray-300">modular trigger sensors: TBD</div>
        </div>
    );
};

export default Page;
