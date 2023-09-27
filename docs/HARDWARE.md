# Hardware Setup
## Prerequisites
- Raspberry Pi Zero W (or Raspberry Pi Zero WH)
- Headers for the Raspberry Pi Zero W if you did not choose a Raspberry Pi Zero WH (if you do not feel comfortable soldering the headers you can use solderless headers such as these [here](https://www.berrybase.de/en/solderless-stiftleiste-2x-20-polig-rm-2-54-gerade))
- Raspberry Pi Camera Module (i chose the [Waveshare RPi Camera (F)](https://www.berrybase.de/en/noir-kamera-fuer-raspberry-pi-mit-einstellbarem-fokus-und-infrarot-leds))
- Flexcable adapter for the camera module (such as this one [here](https://www.berrybase.de/en/flexkabel-fuer-raspberry-pi-zero-und-kameramodul?number=RPIZ-FLEX-15))
- Magnet Reed Switch (i chose the following [KY-025 module](https://www.amazon.de/dp/B089QJVBL7?psc=1&ref=ppx_yo2ov_dt_b_product_details))
- a bunch of Dupont Jumper Wires
- Breadboard (optional)

## Camera
Attach the camera to the Raspberry Pi. You will need a flex cable adapter for the Pi Zero  for the camera module since the Raspberry Pi Zero has a smaller smaller connector than the standard camera module. The camera should be attached to the Raspberry Pi as shown below.

![270868898-25d4370a-b620-4d31-9c9b-fb232d06bef7](https://github.com/infinitel8p/Security-Cam/assets/50703696/3232fdbe-9dc6-491a-aeac-1ead849368fb)

If connected properly you should see a faint red glow from the camera's infrared LEDs when the raspberry is turned on.

### Update the Camera Library
Update the camera library (and everything else) first if you have not already done so. Run the following commands on the Raspberry Pi:
```bash
sudo apt update
sudo apt upgrade
```

### Camera Setup
Edit the `/boot/config.txt` file:
```bash
sudo nano /boot/config.txt
```

Add the following line to the end of the file:
```bash
start_x=1
```

Restart the Raspberry Pi now.

> If you use OV9281, IMX290, IMX378, or non-Raspberry Pi official IMX219 and IMX477 cameras, you need to configure the config.txt file separately:
>```bash
>sudo nano /boot/config.txt
>```
>Find "camera-auto-detect=1" and modify it to "camera_auto_detect=0".
> 
> At the end of the file, add the following setting statements according to the camera model:
> | Camera Model  | Setting Statement                          |
> | ------------- | ------------------------------------------ |
> | OV9281        | dtoverlay=ov9281                           |
> | IMX290/IMX327 | dtoverlay=imx290, clock-frequency=37125000 |
> | IMX477        | dtoverlay=imx477                           |
> | IMX378        | dtoverlay=imx378                           |
> | IMX219        | dtoverlay=imx219                           |


### Test the Camera
The WaveShare RPi Camera (F) has a OV5647 sensor which should be supported by `libcamera` and `Raspicam`.
Depending on your chosen camera module you need to enable legacy camera support so to test the camera, run the following commands on the Raspberry Pi:

```bash
vcgencmd get_camera
```
This should return the following:
```bash
supported=1 detected=1
```
*Note: If it returns `supported=0 detected=0` you need to enable legacy camera support first. See the [section below](#enabling-legacy-camera-support) for instructions on how to do that.*

Now test the camera with the following command:
```bash
raspistill -o test.jpg
```
This should take a picture and save it as `test.jpg` in the current directory.

### Enabling Legacy Camera Support
To enable the legacy camera support, run the following command on the Raspberry Pi:
```bash
sudo raspi-config
```

In the menu, select `Interface Options` and then `Legacy Camera`. Select `Yes` to enable it and then `Ok`. Select `Finish` to exit the configuration menu and reboot the Raspberry Pi.

Test the camera again with the commands from the [section above](#test-the-camera).

## Magnet Reed Switch
If you have a Raspberry Pi Zero W and you have not yet soldered the GPIO header, you can do so now. The magnet reed switch will be connected to the Raspberry Pi as shown below.

![20230927_072021](https://github.com/infinitel8p/Security-Cam/assets/50703696/56c40de5-69e2-4397-9365-49f6284a3ebe)
*Note: This is the connection layout using a breadboard. The magnet reed can also just be connected directly to the Raspberry Pi skipping the breadboard.*

### KY-025 connection
The pinout on the KY-025 module with the already connected jumper wires is shown below.

![image](https://github.com/infinitel8p/Security-Cam/assets/50703696/6ec39776-6104-42eb-9780-88899c248223)

| KY-025 Pin  | Wire              |
| ----------- | ----------------- |
| **GND**     | Black Jumper Wire |
| **DO**      | Blue Jumper Wire  |
| **+ (VCC)** | Red Jumper Wire   |

*Note: The KY-025 module has a fourth pin, marked with `AO`. This is the analog output pin and is not used in this project since the Raspberry Pi does not have an analog input pin and a converter such as the ADS1115 would be required to use it.*

### Raspberry Pi connection
The pinout on the Raspberry Pi with the already connected jumper wires is shown below.

![image](https://github.com/infinitel8p/Security-Cam/assets/50703696/9993c261-44fc-419b-ae6c-81c62854a4c3)

![image](https://github.com/infinitel8p/Security-Cam/assets/50703696/3438075e-0989-4f01-a75a-cd3aa3f42bbd)

| Raspberry Pi Pin    | Wire              |
| ------------------- | ----------------- |
| **[pin 14] GND**    | Black Jumper Wire |
| **[pin 15] GPIO22** | Blue Jumper Wire  |
| **[pin 17] 3V3**    | Red Jumper Wire   |

### Test the Magnet Reed Switch
If connected properly in the previous step, the red LED on the KY-025 module should be lit up when the Raspberry Pi is turned on.  
To test the magnet reed switch, create the following python script on the Raspberry Pi:
```bash
nano test.py
```
Paste the following code into the file:
```python
import RPi.GPIO as GPIO
from time import sleep

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

Digital_Pin = 22
GPIO.setup(Digital_Pin, GPIO.IN)

try:
    while True:
        if GPIO.input(Digital_Pin):
            print("Magnet Detected!")
        else:
            print("No Magnet")
        sleep(1)
except KeyboardInterrupt:
    print("\nScript closed!")

finally:
    GPIO.cleanup()
```

Save the file and exit the editor. Run the script with the following command:
```bash
python3 test.py
```

Now test the switch. When you come near the sensor with a magnet the script should print `Magnet Detected!` if the magnet reed switch is triggered and `No Magnet` if it is not.


Continue to [WIFI.md](WIFI.md) to set up the Raspberry Pi as an access point and connect to it.