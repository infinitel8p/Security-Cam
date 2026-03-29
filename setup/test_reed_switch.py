from gpiozero import DigitalInputDevice
from time import sleep

reed_switch = DigitalInputDevice(22)

try:
    while True:
        if reed_switch.value:
            print("Magnet Detected!")
        else:
            print("No Magnet")
        sleep(1)
except KeyboardInterrupt:
    print("\nScript closed!")
