"use client";
import { fetchDeviceList } from '@/lib/helpers';
import React, { useState, useEffect } from 'react';

const BTDeviceList = () => {
    const [btDevices, setBtDevices] = useState<Device[]>([]);

    useEffect(() => {
        fetchDeviceList(setBtDevices, "BT");
    }, []);

    return (
        <div>
            <h3>Bluetooth Devices: <span className='text-xs'>(need to add pairing and unpairing)</span></h3>
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
