"use client";
import React, { useState, useEffect } from 'react';

const WiFiDeviceList = () => {
    const [wifiDevices, setWifiDevices] = useState([]);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const settingsFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005/settings`;
                const response = await fetch(settingsFeedUrl);
                const data = await response.json();
                setWifiDevices(data.TARGET_AP_MAC_ADDRESSES);
            } catch (error) {
                console.error("Error fetching Wi-Fi devices:", error);
            }
        };

        fetchSettings();
    }, []);

    return (
        <div>
            <h3>Wi-Fi Devices:</h3>
            <ul>
                {wifiDevices.map((device, index) => (
                    <li key={index}>
                        {device.name}: {device.address}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default WiFiDeviceList;
