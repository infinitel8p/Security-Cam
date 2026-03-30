# Security Camera
A security camera system for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).

**Currently WIP**

The system automatically records video when a trigger sensor is activated (e.g. door opened, motion detected) and no tracked device is connected via Bluetooth or WiFi. Recording stops when the sensor resets. The trigger sensor is modular - swap between a magnetic reed switch, PIR motion sensor, push button, or software mock without changing any code.

Integrations:
- **Modular Trigger Sensors**: Pluggable sensor system supporting magnetic reed switches, PIR motion sensors, Hall-effect sensors, vibration/knock sensors, tilt switches, touch sensors, push buttons, and a software mock. Swap hardware without code changes - configure via the dashboard or REST API.
- **Presence-Gated Recording**: Sensor triggers are gated by Bluetooth and WiFi presence detection. If a tracked device (e.g. your phone) is nearby, the trigger is ignored. Manual recording is always allowed.
- **WiFi Detection**: WiFi Access Point integration for device presence detection. Also allows viewing recorded videos from outside the home network.
- **Bluetooth Detection**: Bluetooth integration for device presence detection.
- **Real Time Clock**: DS3231 RTC module keeps accurate time when the Raspberry Pi is powered off.
- **Web Dashboard**: Live camera feed via WebRTC, video archive, system health monitoring, event timeline, device management, and sensor configuration.
- **MediaMTX Streaming**: Hardware-accelerated H.264 camera streaming via WebRTC and RTSP.

## Table of Contents

- [Security Camera](#security-camera)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Setup \& Usage](#setup--usage)
  - [Future Enhancements](#future-enhancements)
  - [Troubleshooting](#troubleshooting)
  - [Contribution Guidelines](#contribution-guidelines)
  - [License](#license)

## Prerequisites

- [Raspberry Pi Zero 2 W](https://www.raspberrypi.com/products/raspberry-pi-zero-2-w/) (or Raspberry Pi Zero 2 WH)
- [Headers](https://amzn.eu/d/hULoAo6) for the Raspberry Pi Zero 2 W if you did not choose a Raspberry Pi Zero 2 WH (if you do not feel comfortable soldering the headers you can use solderless headers such as these [here](https://www.berrybase.de/en/solderless-stiftleiste-2x-20-polig-rm-2-54-gerade))
- [Waveshare RPi Camera (F)](https://www.berrybase.de/en/noir-kamera-fuer-raspberry-pi-mit-einstellbarem-fokus-und-infrarot-leds) or another compatible camera module
- [Flexcable adapter](https://www.berrybase.de/en/flexkabel-fuer-raspberry-pi-zero-und-kameramodul?number=RPIZ-FLEX-15) for the camera module
- Bluetooth-enabled device (e.g., a smartphone) to pair with the Raspberry Pi
- A trigger sensor - any of the [supported modules](https://dev.infinitel8p.com/Security-Cam/basics/sensors) (e.g. KY-025 reed switch, HC-SR501 PIR, or just use the software mock for testing)
- a bunch of [Dupont Jumper Wires](https://amzn.eu/d/6ZgE4N6)
- Breadboard (optional)
- [DS3231 Real Time Clock Module](https://amzn.eu/d/ikNTko8)

## Setup & Usage
Follow the instructions in our [documentation](https://dev.infinitel8p.com/Security-Cam/) to set up the hardware and find out how to use it.

## Future Enhancements
- **Improved Error Handling**: Improved error handling to prevent the script from crashing, server from freezing, etc.

## Troubleshooting
_This section will be populated with common issues and their solutions as they are identified._

## Contribution Guidelines
If you'd like to contribute to this project, please follow the guidelines in the [CONTRIBUTING.md](./CONTRIBUTING.md) file.

## License
This project is licensed under the [MIT License](./LICENSE). Please see the `LICENSE` file for more details.
