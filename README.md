# Security Camera
A security camera script for the Raspberry Pi Zero W using the Waveshare RPi Camera (F).  
The script will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed).

Integrations:
- **Magnetic Reed Switch**: Integration with a magnetic reed switch to detect door open/close events and trigger recording accordingly.
- **WIFI Detection**: Integration with WiFi Access Point to allow user to use bluetooth or WiFi to not trigger recording. Allows user to view recorded videos in the web interface when outside of the home network.
- **Bluetooth Detection**: Integration with Bluetooth to allow user to use bluetooth to not trigger recording.

## Table of Contents

- [Security Camera](#security-camera)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Setup](#setup)
  - [Usage](#usage)
  - [Future Enhancements](#future-enhancements)
  - [Troubleshooting](#troubleshooting)
  - [Contribution Guidelines](#contribution-guidelines)
  - [License](#license)

## Prerequisites

- [Raspberry Pi Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) (or Raspberry Pi Zero WH)
- [Headers](https://amzn.eu/d/hULoAo6) for the Raspberry Pi Zero W if you did not choose a Raspberry Pi Zero WH (if you do not feel comfortable soldering the headers you can use solderless headers such as these [here](https://www.berrybase.de/en/solderless-stiftleiste-2x-20-polig-rm-2-54-gerade))
- [Waveshare RPi Camera (F)](https://www.berrybase.de/en/noir-kamera-fuer-raspberry-pi-mit-einstellbarem-fokus-und-infrarot-leds) or another compatible camera module
- [Flexcable adapter](https://www.berrybase.de/en/flexkabel-fuer-raspberry-pi-zero-und-kameramodul?number=RPIZ-FLEX-15) for the camera module
- Bluetooth-enabled device (e.g., a smartphone) to pair with the Raspberry Pi
- [KY-025 module](https://amzn.eu/d/grjoopD) (Magnetic reed switch)
- a bunch of [Dupont Jumper Wires](https://amzn.eu/d/6ZgE4N6)
- Breadboard (optional)
- [DS3231 Real Time Clock Module](https://amzn.eu/d/ikNTko8)

## Setup
The following sections will explain how to set up the Raspberry Pi Zero W. It is assumed that the Raspberry Pi Zero W is already set up and running (Optional - set up VNC if you have a hard time working in a headless setup). If you need help setting up the Raspberry Pi Zero W, please refer to the [Raspberry Pi Documentation](https://www.raspberrypi.org/documentation/).

1. ### Hardware setup
    The Instructions to the hardware setup can be found [here](./documentation/docs/setup/hardware.mdx). If you are new to the project, please start here.  
    They explain how to connect the camera module and the magnetic reed switch to the Raspberry Pi and serve as entry point to the project.
2. ### WiFi setup
    The Instructions to the WiFi setup can be found [here](./documentation/docs/setup/wifi.mdx).  
    They explain how to set up the Raspberry Pi as an access point and how to connect to it. This will be necessary to connect to the Raspberry Pi when outside of the home network and to access the web interface.
3. ### Bluetooth and Script setup
    The Instructions to the Bluetooth setup and the script setup can be found [here](./documentation/docs/setup/script.mdx).
    They explain how to pair the Raspberry Pi with a Bluetooth device and how to set up the script.


## Usage
Once the script is running, the Raspberry Pi will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed). 

## Future Enhancements
- **Web Interface**: A user-friendly interface to view recorded videos. **_WIP_**.
- **Captive Portal**: Captive portal to open Web Interface when connecting to the Raspberry Pi's WiFi.
- **System Monitor**: A system monitor to view the status of the Raspberry Pi (e.g., CPU temperature, CPU usage, RAM usage, etc.).
- **Improved Error Handling**: Improved error handling to prevent the script from crashing, server from freezing, etc.

## Troubleshooting
_This section will be populated with common issues and their solutions as they are identified._

## Contribution Guidelines
If you'd like to contribute to this project, please follow these guidelines:

1. **Fork the Repository**: Create a fork of this repository to your account.
2. **Clone the Fork**: Clone the forked repository to your local machine.
3. **Create a New Branch**: Always create a new branch for your changes.
4. **Make Changes**: Implement your changes, enhancements, or bug fixes.
5. **Commit and Push**: Commit your changes and push them to your fork.
6. **Create a Pull Request**: Create a pull request from your fork to the main repository.

## License
This project is licensed under the [MIT License](../LICENSE). Please see the `LICENSE` file for more details.