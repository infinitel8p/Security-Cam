---
sidebar_position: 1
---

# Intro
A security camera script for the Raspberry Pi Zero 2 W using the Waveshare RPi Camera (F).  
The script will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed).

Integrations:
- **Magnetic Reed Switch**: Integration with a magnetic reed switch to detect door open/close events and trigger recording accordingly.
- **WIFI Detection**: Integration with WiFi Access Point to allow user to use WiFi to not trigger recording. Allows user to view recorded videos in the web interface when outside of the home network.
- **Bluetooth Detection**: Integration with Bluetooth to allow user to use bluetooth to not trigger recording.
- **Real Time Clock**: Integration with a Real Time Clock to keep track of the time when the Raspberry Pi is powered off.
- **Web Dashboard**: A web dashboard to view the status of the Raspberry Pi and the recorded videos.

## Usage
Once the script is running, the Raspberry Pi will start recording a video when the magnetic reed switch is triggered (the door is opened) and the smartphone is not connected to the Raspberry Pi (bluetooth and/or WiFi). The recording will stop when the magnetic reed switch is triggered again (the door is closed). 
Find out more about the usage [here](./basics/start).

## Future Enhancements
- **Web Interface**: A user-friendly interface to view recorded videos. **_WIP_**.
- **Captive Portal**: Captive portal to open Web Interface when connecting to the Raspberry Pi's WiFi.
- **System Monitor**: A system monitor to view the status of the Raspberry Pi (e.g., CPU temperature, CPU usage, RAM usage, etc.). **_WIP (included in the dashboard)_**.
- **Improved Error Handling**: Improved error handling to prevent the script from crashing, server from freezing, etc.

## Troubleshooting
_This section will be populated with common issues and their solutions as they are identified._

## Contribution Guidelines
If you'd like to contribute to this project, please follow the guidelines in the [CONTRIBUTING.md](https://github.com/infinitel8p/Security-Cam/blob/main/CONTRIBUTING.md) file.

## License
This project is licensed under the [MIT License](https://github.com/infinitel8p/Security-Cam/blob/main/LICENSE). Please see the `LICENSE` file for more details.