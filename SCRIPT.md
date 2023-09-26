
## Install 

To set up the necessary libraries and tools, run the following commands:

```bash
sudo apt-get update
sudo apt-get install python3-picamera
sudo apt-get install python3-pip
sudo pip3 install pybluez
```

## Setup
1. #### Modify the Script
   - Open the main.py file in an editor.
   - Locate the line TARGET_BT_ADDRESS = "XX:XX:XX:XX:XX:XX".
   - Replace XX:XX:XX:XX:XX:XX with the Bluetooth MAC address of your device (e.g., your smartphone).
2. #### Pairing
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
   - Exit `bluetoothctl`.
3. #### Run the Script
   - Start the security camera script with the following command:
       ```bash
       python3 main.py
       ```