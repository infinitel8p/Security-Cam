'use client';
import React, { useState, useEffect } from "react";

const Page = () => {
    const [settings, setSettings] = useState({
        VideoSaveLocation: "Loading...",
    });
    const [newLocation, setNewLocation] = useState("");

    useEffect(() => {
        const settingsFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005/settings`;

        const fetchSettingsInfo = async () => {
            try {
                const response = await fetch(settingsFeedUrl);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                const data = await response.json();
                console.log("Fetched Settings Info:", data);
                setSettings(data);
            } catch (error) {
                console.error("Error fetching settings info:", error);
                setSettings({
                    VideoSaveLocation: "Error loading data",
                });
            }
        };

        fetchSettingsInfo();
    }, []);

    const handleSaveLocationChange = async () => {
        const settingsFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005/settings`;
        try {
            const response = await fetch(settingsFeedUrl, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({ VideoSaveLocation: newLocation }),
            });

            const result = await response.json();
            if (!response.ok) {
                alert(result.message || "Error updating settings");
            } else {
                alert("Settings updated successfully");
                setSettings(prevSettings => ({ ...prevSettings, VideoSaveLocation: newLocation }));
            }
        } catch (error) {
            console.error("Error updating settings:", error);
            alert("Error updating settings");
        }
    };

    return (
        <div>
            <div>bt device mac</div>
            <div>wifi device mac</div>
            <div>{`Video save location: ${settings.VideoSaveLocation}`}</div>
            <div>
                <input
                    type="text"
                    value={newLocation}
                    onChange={(e) => setNewLocation(e.target.value)}
                    placeholder="Enter new video save location"
                />
                <button onClick={handleSaveLocationChange}>Update Location</button>
            </div>
            <div className="text-gray-300">modular trigger sensors: TBD</div>
        </div>
    );
};

export default Page;
