# Security Camera
A security camera script for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).  

**Currently WIP ⚠**

The script will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed).

Integrations:
- **Magnetic Reed Switch**: Integration with a magnetic reed switch to detect door open/close events and trigger recording accordingly.
- **WIFI Detection**: Integration with WiFi Access Point to allow user to use bluetooth or WiFi to not trigger recording. Allows user to view recorded videos in the web interface when outside of the home network.
- **Bluetooth Detection**: Integration with Bluetooth to allow user to use bluetooth to not trigger recording.
- **Real Time Clock**: Integration with a Real Time Clock to keep track of the time when the Raspberry Pi is powered off.
- **Web Dashboard**: A web dashboard to view the status of the Raspberry Pi and the recorded videos.

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
- [KY-025 module](https://amzn.eu/d/grjoopD) (Magnetic reed switch)
- a bunch of [Dupont Jumper Wires](https://amzn.eu/d/6ZgE4N6)
- Breadboard (optional)
- [DS3231 Real Time Clock Module](https://amzn.eu/d/ikNTko8)

## Setup & Usage
Follow the instructions in our [documentation](https://dev.infinitel8p.com/Security-Cam/) to set up the hardware and find out how to use it.

## Future Enhancements
- **Web Interface**: A user-friendly interface to view recorded videos. **_WIP_**.
- **Captive Portal**: Captive portal to open Web Interface when connecting to the Raspberry Pi's WiFi.
- **System Monitor**: A system monitor to view the status of the Raspberry Pi (e.g., CPU temperature, CPU usage, RAM usage, etc.). **_WIP (included in the dashboard)_**.
- **Improved Error Handling**: Improved error handling to prevent the script from crashing, server from freezing, etc.

## Troubleshooting
_This section will be populated with common issues and their solutions as they are identified._

## Contribution Guidelines
If you'd like to contribute to this project, please follow the guidelines in the [CONTRIBUTING.md](./CONTRIBUTING.md) file.

## License
This project is licensed under the [MIT License](./LICENSE). Please see the `LICENSE` file for more details.
