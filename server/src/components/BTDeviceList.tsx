"use client";
import React, { useState, useEffect } from 'react';

const BTDeviceList = () => {
    const [btDevices, setBtDevices] = useState([]);

    useEffect(() => {
        const fetchSettings = async () => {
            try {
                const settingsFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005/settings`;
                const response = await fetch(settingsFeedUrl);
                const data = await response.json();
                setBtDevices(data.TARGET_BT_ADDRESSES);
            } catch (error) {
                console.error("Error fetching BT devices:", error);
            }
        };

        fetchSettings();
    }, []);

    return (
        <div>
            <h3>Bluetooth Devices:</h3>
            <ul>
                {btDevices.map((device, index) => (
                    <li key={index}>
                        {device.name}: {device.address}
                    </li>
                ))}
            </ul>
        </div>
    );
};

export default BTDeviceList;
