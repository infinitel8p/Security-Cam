'use client';
import React, { useState, useEffect } from "react";

const SystemMonitor = () => {
    const [systemInfo, setSystemInfo] = useState({
        cpu_temp_celsius: "Loading...",
        cpu_load_percent: "Loading...",
        storage_info_gb: { total_gb: "Loading...", used_gb: "Loading..." },
        ram_usage_mb: { total_mb: "Loading...", used_mb: "Loading..." },
    });

    const systemFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005/system_info`;

    useEffect(() => {
        const fetchSystemInfo = async () => {
            try {
                const response = await fetch(systemFeedUrl);
                const data = await response.json();
                setSystemInfo(data);
            } catch (error) {
                console.error("Error fetching system info:", error);
            }
        };

        fetchSystemInfo();
    }, [systemFeedUrl]);

    return (
        <div className="grid grid-cols-3 border border-red-200 gap-10">
            <div className="border border-red-500 text-center">Temp: {systemInfo.cpu_temp_celsius}°C</div>
            <div className="border border-red-500 text-center">CPU: {systemInfo.cpu_load_percent}%</div>
            <div className="border border-red-500 text-center">
                Storage: {systemInfo.storage_info_gb.used_gb} GB / {systemInfo.storage_info_gb.total_gb} GB
            </div>
            <div className="border border-red-500 text-center">
                RAM: {systemInfo.ram_usage_mb.used_mb} MB / {systemInfo.ram_usage_mb.total_mb} MB
            </div>
        </div>
    );
};

export default SystemMonitor;
