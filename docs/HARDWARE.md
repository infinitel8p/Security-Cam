# Hardware Setup

## Table of Contents
- [Hardware Setup](#hardware-setup)
  - [Table of Contents](#table-of-contents)
  - [Prerequisites](#prerequisites)
  - [Camera](#camera)
    - [Update the Camera Library](#update-the-camera-library)
    - [Camera Setup](#camera-setup)
    - [Test the Camera](#test-the-camera)
    - [Enabling Legacy Camera Support](#enabling-legacy-camera-support)
  - [Magnet Reed Switch](#magnet-reed-switch)
    - [KY-025 connection](#ky-025-connection)
    - [Raspberry Pi connection](#raspberry-pi-connection)
    - [Test the Magnet Reed Switch](#test-the-magnet-reed-switch)
  - [Real Time Clock Module](#real-time-clock-module)
    - [DS3231 connection](#ds3231-connection)
    - [Raspberry Pi connection](#raspberry-pi-connection-1)
    - [Enable I2C Interface](#enable-i2c-interface)

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


## Real Time Clock Module
### DS3231 connection
The pinout on the DS3231 module is shown below.  

<div style="display: flex;">
<img src="https://github.com/infinitel8p/Security-Cam/assets/50703696/23d48c70-2e41-4f6f-baf1-836163926949" alt="Image 1" width="400" />
    <img src="https://github.com/infinitel8p/Security-Cam/assets/50703696/be0c37e0-1c15-44e3-8dba-51f63615c5c3" alt="Image 2" width="400" />
</div>

| DS3231 Pin | Wire        |
| ---------- | ----------- |
| **3.3V**   | Red Wire    |
| **SDA**    | Orange Wire |
| **NC**     | -           |
| **SCK**    | Yellow Wire |
| **GND**    | Green Wire  |


*Note: The DS3231 module has a fifth pin, marked with `NC`. This "NC" (Not Connected) pin is not used or connected to anything.*

### Raspberry Pi connection

![20230927_172741](https://github.com/infinitel8p/Security-Cam/assets/50703696/b1fa89fb-877d-44ab-9870-e8b178a2d528)

<div style="display: flex; align-items: center;">
  <!-- Table -->
  <div style="flex: 1; margin-right: 20px;">
    <table>
      <tr>
        <th>Raspberry Pi Pin</th>
        <th>Wire</th>
      </tr>
      <tr>
        <td><strong>[pin 1] 3V3</strong></td>
        <td>Red Wire</td>
      </tr>
      <tr>
        <td><strong>[pin 3] SDA</strong></td>
        <td>Orange Wire</td>
      </tr>
      <tr>
        <td><strong>[pin 5] SCL</strong></td>
        <td>Yellow Wire</td>
      </tr>
      <tr>
        <td><strong>[pin 6 or 9] GND</strong></td>
        <td>Green Wire</td>
      </tr>
    </table>  
 
*Note: for the connections on the Raspberry you can refer the diagram shown [here](#raspberry-pi-connection) again*

  </div>
  <!-- Image -->
  <div style="flex: 1;">
    <img src="https://github.com/infinitel8p/Security-Cam/assets/50703696/b317925d-4eb0-4f59-a70e-86bfebb64f05" alt="Image 2" width="400" />
  </div>
</div>

*Note: This is the connection layout using a breadboard. The clock can also just be connected directly to the Raspberry Pi skipping the breadboard as shown below.*

![61JfhAHWeKL _AC_SX679_](https://github.com/infinitel8p/Security-Cam/assets/50703696/40ddedeb-509f-41e2-b50f-63aa0e9d1f3e)

### Enable I2C Interface
1. #### To enable the I2C interface, run the following command on the Raspberry Pi:
    ```bash
    sudo raspi-config
    ```

    In the menu, select `Interface Options` and then `I2C`. Select `Yes` to enable it and then `Ok`. Select `Finish` to exit the configuration menu and reboot the Raspberry Pi.

2. #### Install the required packages:
    ```bash
    sudo apt-get update
    sudo apt-get install python3-smbus
    sudo apt-get install i2c-tools
    ```

3. #### Test the DS3231 RTC module:
    You can use the `sudo i2cdetect -y 1` command to see if your Raspberry Pi detects the DS3231 RTC.  
    You should see a number (usually 68 or 0x68) in the grid that corresponds to the module's address:
    ```bash
    pi@raspberrypizero2:~ $ sudo i2cdetect -y 1
         0  1  2  3  4  5  6  7  8  9  a  b  c  d  e  f
    00:                         -- -- -- -- -- -- -- --
    10: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    20: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    30: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    40: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    50: -- -- -- -- -- -- -- -- -- -- -- -- -- -- -- --
    60: -- -- -- -- -- -- -- -- 68 -- -- -- -- -- -- --
    70: -- -- -- -- -- -- -- --
    ```

4. #### Configure the I2C-Bus for the x68 address:
    ```bash
    echo ds3231 0x68 | sudo tee /sys/class/i2c-adapter/i2c-1/new_device
    ```	

    `sudo hwclock` should now return the time from the RTC.

5. #### Set the System Time:
    Synchronize the RTC time:
    ```bash
    sudo hwclock -w
    ```
    This will set the hardware clock to the current system time.

6. #### Enable automatic bus configuration:
    ```bash
    sudo nano /etc/rc.local
    ```

    At the end of the file **before** `exit 0`, add the following line:
    ```bash
    echo ds3231 0x68 > /sys/class/i2c-adapter/i2c-1/new_device
    ```

7. #### Disable the fake-hwclock:
    ```bash
    sudo systemctl disable fake-hwclock
    sudo systemctl stop fake-hwclock
    ```
    This will prevent the fake-hwclock from overwriting the hardware clock at boot.
    If you have internet and want to sync the RTC time with the time servers, you can manually run the following command:
    ```bash
    sudo hwclock -w
    ```

8. #### Reboot the Raspberry Pi:
    ```bash
    sudo reboot
    ```

With the RTC module connected and configured, the Raspberry Pi will now use the RTC module to keep track of the time even when it is turned off.

Continue to [WIFI.md](./WIFI.md) to set up the Raspberry Pi as an access point and connect to it.