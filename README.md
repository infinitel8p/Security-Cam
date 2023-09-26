# Security Camera
A security camera script for the Raspberry Pi Zero W using the Waveshare RPi Camera (F).  
This script allows the Raspberry Pi to start recording video and pause the recording when it's actively connected to a specified Bluetooth device, such as a smartphone.  
  
This script will be modified; I intend to add a web interface (to start and stop the recording and to view the recorded videos), add a magnetic reed switch to the Raspberry Pi to detect if the door is open or closed and a hardware clock to keep track of the date and time even when the Raspberry Pi has been powered off.  
The script will start recording when the door is opened but only if the smartphone is not connected to the Raspberry Pi.

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

- Raspberry Pi Zero W (or Raspberry Pi Zero WH)
- Waveshare RPi Camera (F) or compatible camera module
- Bluetooth-enabled device (e.g., a smartphone) to pair with the Raspberry Pi
- _Magnetic reed switch (optional)_ - will be added in the future
- _Hardwareclock (optional)_ - will be added in the future

## Setup

1. ### WiFi setup
    The Instructions to the WiFi setup can be found [here](WIFI.md).  
    They explain how to set up the Raspberry Pi as an access point and how to connect to it. This will be necessary to connect to the Raspberry Pi when outside of the home network and to access the web interface.
2. ### Bluetooth and Script setup
    The Instructions to the Bluetooth setup and the script setup can be found [here](SCRIPT.md).
    They explain how to pair the Raspberry Pi with a Bluetooth device and how to set up the script.


## Usage
Once the script is running, the Raspberry Pi will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed). 

## Future Enhancements
- **Magnetic Reed Switch**: Integration with a magnetic reed switch to detect door open/close events and trigger recording accordingly.
- **WIFI Detection**: Integration with WiFi Access Point to allow user to use bluetooth or WiFi to trigger recording. Allows user to view recorded videos in the web interface when outside of the home network.
- **Web Interface**: A user-friendly interface to view recorded videos.
- **Hardware Clock**: Integration with a hardware clock to keep track of the date and time even when the Raspberry Pi has been powered off.

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