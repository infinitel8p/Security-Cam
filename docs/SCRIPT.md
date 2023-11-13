# Bluetooth & Script Setup
## Install 

To set up the necessary libraries and tools, run the following commands:

```bash
sudo apt-get update
sudo apt-get install python3-picamera
sudo apt-get install python3-pip
```

Now clone the repository and install the required Python libraries:

```bash
git clone https://github.com/infinitel8p/Security-Cam/
cd Security-Cam
sudo pip3 install -r requirements.txt
```

## Pairing
- Ensure your Bluetooth device's visibility is turned on.
- On the Raspberry Pi, run `bluetoothctl`.
- In the bluetoothctl prompt, enter the following commands:
   ```bash
   agent on
   default-agent
   scan on
   ```
- Once you see the MAC address of your device, pair with it using: `pair XX:XX:XX:XX:XX:XX`.
- Trust the device using: `trust XX:XX:XX:XX:XX:XX`.
- `exit` from `bluetoothctl`.

## Setup
1. #### Modify the Script
   - Open the `config.json` file.
   - Replace XX:XX:XX:XX:XX:XX with the Bluetooth MAC address of your device (e.g., your smartphone).
   - Replace XX:XX:XX:XX:XX:XX with the WiFi MAC address of your device (e.g., your smartphone).
   
   Your `config.json` could look like this:
    | example 1                                                                                                                                                                    | example 2                                                                                                                                                                                                                          |
    | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
    | <pre lang="json">{<br>    "TARGET_BT_ADDRESSES": [<br>    "12:34:56:78:9A:BC",<br>    ],<br>    "TARGET_AP_MAC_ADDRESSES": [<br>    "A1:B2:C3:D4:E5:F6",<br>    ]<br>}</pre> | <pre lang="json">{<br>    "TARGET_BT_ADDRESSES": [<br>    "12:34:56:78:9A:BC",<br>    "DE:F1:23:45:67:89"<br>    ],<br>    "TARGET_AP_MAC_ADDRESSES": [<br>    "A1:B2:C3:D4:E5:F6",<br>    "F6:E5:D4:C3:B2:A1"<br>    ]<br>}</pre> |

2. #### Run the Script
   - Start the security camera script with the following command:
       ```bash
       python3 main.py
       ```

## Install Node.js
- Install Node.js with the following commands:
   1. Update the Raspberry Pi
      ```bash
      sudo apt update
      sudo apt upgrade
      ```
   2. Check the Node.js Version Available
      ```bash
      apt-cache policy nodejs
      ```
      The output should look like this:
      ```bash
      pi@raspberrypizero2:~ $ apt-cache policy nodejs
      nodejs:
      Installed: (none)
      Candidate: 12.22.12~dfsg-1~deb11u4
      Version table:
         12.22.12~dfsg-1~deb11u4 500
            500 http://raspbian.raspberrypi.org/raspbian bullseye/main armhf Packages
      ```
      The apt-cache policy nodejs command shows that Node.js version 12.22.12 is available for installation from the Raspberry Pi repositories, but it hasn't been installed (Installed: (none)).
   3. Install Node.JS and npm on the Raspberry Pi
      ```bash
      sudo apt install nodejs
      sudo apt install npm
      ```
   4. Check the version
      ```bash
      nodejs -v  # Checks Node.js version
      npm -v     # Checks npm version
      ```

## Install FFmpeg
- Install FFmpeg with the following commands:
   1. Install FFmpeg
      ```bash
      sudo apt-get update
      sudo apt-get install ffmpeg
      ```
   2. Check the version
      ```bash
      ffmpeg -version
      ```