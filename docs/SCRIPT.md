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