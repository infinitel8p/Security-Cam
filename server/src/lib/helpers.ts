export async function fetchDeviceList(setDevices: (devices: Device[]) => void, deviceType: string) {
    try {
        const settingsFeedUrl = `${window.location.protocol}//${window.location.hostname}:5005/settings`;
        const response = await fetch(settingsFeedUrl);
        const data = await response.json();
        setDevices(data[`TARGET_${deviceType}_ADDRESSES`]);
    } catch (error) {
        console.error(`Error fetching ${deviceType} devices:`, error);
    }
}