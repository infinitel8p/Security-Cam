---
sidebar_position: 1
---

# Intro

A security camera system for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).

The system automatically records video when a trigger sensor is activated (e.g. door opened, motion detected) and no tracked device is connected via Bluetooth or WiFi. Recording stops when the sensor resets. The trigger sensor is modular - swap between a magnetic reed switch, PIR motion sensor, vibration sensor, or any of the supported modules without changing any code.

## Features

- **Modular Trigger Sensors** - 11 sensor types including magnetic reed switches, PIR motion, vibration/knock, tilt, touch, light gates, and a software mock. [Calibration](./basics/calibration) sliders let you fine-tune sensitivity and thresholds.
- **Presence-Gated Recording** - sensor triggers are gated by Bluetooth and WiFi presence detection. If a tracked device (e.g. your phone) is nearby, the trigger is suppressed. Manual recording is always allowed.
- **Auto-Delete Storage** - automatically removes oldest recordings when disk usage exceeds a configurable threshold. Supports network storage (NFS/SMB).
- **Web Dashboard** - live camera feed via WebRTC (HLS fallback), video archive, system health monitoring, event timeline, activity heatmap, and device management. Dark and light themes, 5 languages.
- **MediaMTX Streaming** - hardware-accelerated H.264 camera streaming via WebRTC and RTSP.
- **WiFi & Bluetooth Detection** - presence detection via WiFi Access Point and Bluetooth.
- **Real Time Clock** - DS3231 RTC module keeps accurate time when the Pi is powered off.

## Getting started

1. Follow the [Setup guide](./category/setup) to configure your hardware, WiFi, Bluetooth, and streaming
2. Open the [Dashboard](./basics/dashboard) to start using the system
3. Configure [Trigger Sensors](./basics/sensors) and [Calibration](./basics/calibration) for automatic recording

## Contributing

If you'd like to contribute to this project, please follow the guidelines in the [CONTRIBUTING.md](https://github.com/infinitel8p/Security-Cam/blob/main/CONTRIBUTING.md) file.

## License

This project is licensed under the [MIT License](https://github.com/infinitel8p/Security-Cam/blob/main/LICENSE).
