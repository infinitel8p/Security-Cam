"use client";
import React, { useState, useEffect } from 'react';
import { fetchDeviceList } from '@/lib/helpers';

const WiFiDeviceList = () => {
    const [wifiDevices, setWifiDevices] = useState<Device[]>([]);
    
    useEffect(() => {
        fetchDeviceList(setWifiDevices, "AP_MAC");
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
