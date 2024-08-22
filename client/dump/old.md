
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

## Install GPAC

- Install GPAC with the following commands:
  1.  Install GPAC
      ```bash
      sudo apt-get update
      sudo apt-get install gpac
      ```
  1.  Check if GPAC is installed
      ```bash
      gpac
      ```
## Script Setup

1. #### Modify the Script

   - Open the `config.json` file.
   - Replace XX:XX:XX:XX:XX:XX with the Bluetooth MAC address of your device (e.g., your smartphone).
   - Replace XX:XX:XX:XX:XX:XX with the WiFi MAC address of your device (e.g., your smartphone).

   Your `config.json` could look like this:

   ```json
   {
   	"TARGET_BT_ADDRESSES": ["12:34:56:78:9A:BC"],
   	"TARGET_AP_MAC_ADDRESSES": ["A1:B2:C3:D4:E5:F6"]
   }
   ```

   ```json
   {
   	"TARGET_BT_ADDRESSES": ["12:34:56:78:9A:BC", "DE:F1:23:45:67:89"],
   	"TARGET_AP_MAC_ADDRESSES": ["A1:B2:C3:D4:E5:F6", "F6:E5:D4:C3:B2:A1"]
   }
   ```

1. #### Run the Script
   - Start the security camera script from within the `Security-Cam/` folder with thefollowing command:
     ```bash
     python3 main.py
     ```
   - Now startt the server with the following command:
     ```bash
     node ./server/server.js
     ```

## Install Node.js

Install Node.js with the following commands:

```bash
sudo apt update
sudo apt install nodejs npm
```

Check the installed version:

```bash
nodejs -v  # Checks Node.js version
npm -v     # Checks npm version
```

My raspberry pi is running on Node.js `v18.19.0` and npm `9.2.0`.

