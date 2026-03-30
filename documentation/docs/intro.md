---
sidebar_position: 1
---

# Intro
A security camera system for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).
The system automatically records video when a trigger sensor is activated (e.g. door opened, motion detected) and no tracked device is connected via Bluetooth or WiFi. Recording stops when the sensor resets. The trigger sensor is modular - swap between a magnetic reed switch, PIR motion sensor, vibration sensor, or any of the supported modules without changing any code.

Integrations:
- **Modular Trigger Sensors**: Pluggable sensor system supporting magnetic reed switches, PIR motion sensors, Hall-effect sensors, vibration/knock sensors, light gates, tilt switches, touch sensors, push buttons, and a software mock. Swap hardware without code changes - configure via the dashboard or REST API.
- **Presence-Gated Recording**: Sensor triggers are gated by Bluetooth and WiFi presence detection. If a tracked device (e.g. your phone) is nearby, the trigger is ignored. Manual recording is always allowed.
- **WiFi Detection**: WiFi Access Point integration for device presence detection. Also allows viewing recorded videos from outside the home network.
- **Bluetooth Detection**: Bluetooth integration for device presence detection.
- **Real Time Clock**: DS3231 RTC module keeps accurate time when the Raspberry Pi is powered off.
- **Web Dashboard**: Live camera feed via WebRTC, video archive, system health monitoring, event timeline, device management, and sensor configuration - all from a single page.
- **MediaMTX Streaming**: Hardware-accelerated H.264 camera streaming via WebRTC and RTSP using MediaMTX.

## Usage
Once set up, the system runs automatically. The dashboard gives you a live camera feed, recording controls, system health, sensor status, and a video archive. Sensor-triggered recording works in the background - the sensor fires, presence is checked, and if nobody is home, recording starts. Configure everything from the dashboard Settings page: sensor type, GPIO pin, hold timeout, tracked devices, camera settings, and video save location.

Find out more about usage [here](./basics/start).

## Future Enhancements
- **Improved Error Handling**: Improved error handling to prevent the script from crashing, server from freezing, etc.

## Troubleshooting
_This section will be populated with common issues and their solutions as they are identified._

## Contribution Guidelines
If you'd like to contribute to this project, please follow the guidelines in the [CONTRIBUTING.md](https://github.com/infinitel8p/Security-Cam/blob/main/CONTRIBUTING.md) file.

## License
This project is licensed under the [MIT License](https://github.com/infinitel8p/Security-Cam/blob/main/LICENSE). Please see the `LICENSE` file for more details.
