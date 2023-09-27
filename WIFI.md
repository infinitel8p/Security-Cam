# WiFi Setup
1. ### Find your Raspberry's MAC address with `iw dev`:  
    ```bash
    pi@raspberrypizero2:~ $ iw dev
    phy#0
        Unnamed/non-netdev interface
                wdev 0x2
                addr ba:27:xx:xx:xx:xx
                type P2P-device
                txpower 31.00 dBm
        Interface wlan0
                ifindex 2
                wdev 0x1
                addr b8:27:xx:xx:xx:xx
                ssid FRITZ!Box 0420
                type managed
                channel 1 (2412 MHz), width: 20 MHz, center1: 2412 MHz
                txpower 31.00 dBm
    ```
    The MAC address of the `wlan0` interface is `b8:27:xx:xx:xx:xx` in this case.  
    *Note: Remember the channel number (1 in this case) for later.*

1. ### Allocate a device for the AP:  
    This will create a new interface called `ap0` with the same MAC address as `wlan0`. `ap0` will then be the interface used for the AP.
    ```bash
    sudo nano /etc/udev/rules.d/70-persistent-net.rules
    ```

    Add the following lines and **replace your MAC address** accordingly:
    ```bash
    SUBSYSTEM=="ieee80211", ACTION=="add|change", ATTR{macaddress}=="b8:27:xx:xx:xx:xx", KERNEL=="phy0", \
    RUN+="/sbin/iw phy phy0 interface add ap0 type __ap", \
    RUN+="/bin/ip link set ap0 address b8:27:xx:xx:xx:xx"
    ```

3. ### Install `Dnsmasq` and `Hostapd`:
    ```bash
    sudo apt-get update
    sudo apt-get upgrade #Optional
    sudo apt-get install dnsmasq hostapd
    ```

4. ### Configure `Dnsmasq`:
    1. #### Backup the original `dnsmasq` configuration:
        ```bash
        sudo cp /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
        ```

    2. #### Create a new `dnsmasq` configuration:
        ```bash
        sudo nano /etc/dnsmasq.conf
        ```

    3. #### Add the following content:
        ```conf
        interface=lo,ap0
        no-dhcp-interface=lo,wlan0
        bind-interfaces
        server=8.8.8.8
        domain-needed
        bogus-priv
        dhcp-range=192.168.10.50,192.168.10.150,12h
        ```

5. ### Configure `Hostapd`:
    1. #### Open the configuration file:
        ```bash
        sudo nano /etc/hostapd/hostapd.conf
        ```

    2. #### Add the following content:
        ```conf
        ctrl_interface=/var/run/hostapd
        ctrl_interface_group=0
        interface=ap0
        driver=nl80211
        ssid=DevAccessPoint
        hw_mode=g
        channel=1
        wmm_enabled=0
        macaddr_acl=0
        auth_algs=1
        wpa=2
        wpa_passphrase=YourPassPhraseHere
        wpa_key_mgmt=WPA-PSK
        wpa_pairwise=TKIP CCMP
        rsn_pairwise=CCMP
        ```
        Before you save, make sure to do these changes to the configuration:
        1. Replace `DevAccessPoint` and `YourPassPhraseHere` with your desired values
        2. Replace the `channel` with the channel your `wlan0` was running on (as reported by `iw dev` in step 1)

    3. #### Specify where `hostapd` should find its configuration:
        ```bash
        sudo nano /etc/default/hostapd
        ```

        Find the line with `#DAEMON_CONF=""` and replace _(uncomment it or add it if it doesn't exist)_ it with: 
        ```bash
        DAEMON_CONF="/etc/hostapd/hostapd.conf"
        ```

6. ### Modify `wpa_supplicant`:
    1. #### Open the configuration file:
        ```bash
        sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
        ```
    
    2. #### Add the following content (if it doesn't exist already):
        ```conf
        country=US
        ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
        update_config=1

        network={
            ssid="YourSSID1"
            psk="YourPassphrase1"
            id_str="AP1"
        }

        network={
            ssid="YourSSID2"
            psk="YourPassphrase2"
            id_str="AP2"
        }
        ```
        Replace `YourSSID1` and `YourPassphrase1` with your WiFi's SSID and passphrase.
        You can add as many networks as you want, just make sure to increment the `id_str` value for each network. You are are not required to keep `YourSSID2` in the configuration if you only have one WiFi network you want to connect to.  
        Change your country code accordingly.

7. ### Modify `/etc/network/interfaces` to support the new AP
    1. #### Open the configuration file:
        ```bash
        sudo nano /etc/network/interfaces
        ```
    
    2. #### Add the following content:
        ```conf
        auto lo
        auto ap0
        auto wlan0
        iface lo inet loopback

        allow-hotplug ap0
        iface ap0 inet static
            address 192.168.10.1
            netmask 255.255.255.0
            hostapd /etc/hostapd/hostapd.conf

        allow-hotplug wlan0
        iface wlan0 inet manual
            wpa-roam /etc/wpa_supplicant/wpa_supplicant.conf
        iface AP1 inet dhcp
        iface AP2 inet dhcp
        ```

8. ### Start both interfaces:
    ```bash
    sudo ifdown --force wlan0
    sudo ifdown --force ap0
    sudo ifup ap0
    sudo ifup wlan0
    ```

    *Note: It's crucial to copy and paste the entire block of commands above all at once. Executing them one by one will disconnect you from the Pi after disabling the interfaces, preventing you from re-enabling them immediately.
    If your Raspberry Pi Zero W does not reconnect to your WiFi network at this point, unplug the power and plug it back in.  
    On my setup it wouldn't connect even after a restart. I inserted the microSD card into my PC and recreated the `wpa_supplier.conf` in the boot drive.*

9. ### Check the interfaces:
    1. SSH into the Pi again and check the interfaces:
        ```bash
        pi@raspberrypi:~$ ip addr
        1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN group default qlen 1000
            link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
            inet 127.0.0.1/8 scope host lo
            valid_lft forever preferred_lft forever
            inet6 ::1/128 scope host
            valid_lft forever preferred_lft forever
        2: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
            link/ether b8:27:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
            inet 192.168.178.102/24 brd 192.168.178.255 scope global dynamic noprefixroute wlan0
            valid_lft 863907sec preferred_lft 755907sec
            inet6 2a02:4500:4507:8d04:e2455:6452:6e45:2f66/64 scope global dynamic mngtmpaddr noprefixroute
            valid_lft 7102sec preferred_lft 2496sec
            inet6 fe45::4455:a1e3:45c9:5451/64 scope link
            valid_lft forever preferred_lft forever
        3: ap0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc pfifo_fast state UP group default qlen 1000
            link/ether b8:27:xx:xx:xx:xx brd ff:ff:ff:ff:ff:ff
            inet 192.168.10.1/24 brd 192.168.10.255 scope global ap0
            valid_lft forever preferred_lft forever
            inet 169.254.165.183/16 brd 169.254.255.255 scope global noprefixroute ap0
            valid_lft forever preferred_lft forever
            inet6 fe45::7d45:45b8:b45:2f45/64 scope link
            valid_lft forever preferred_lft forever
            inet6 fe45::ba27:eb45:fe7c:3cea/64 scope link
            valid_lft forever preferred_lft forever
        ```
        You should see both `wlan0` and `ap0` interfaces with their respective IP addresses.
        If you scan for WiFi networks with your phone you should also see the `DevAccessPoint` (or whatever you've called it) network.

10. ### Bridge traffic between AP and Client side
    1.  #### Enbale ip-forwarding:
        ```bash
        sudo sysctl -w net.ipv4.ip_forward=1
        ```
    2.  #### Add iptables rules:
        ```bash
        sudo iptables -t nat -A POSTROUTING -s 192.168.10.0/24 ! -d 192.168.10.0/24 -j MASQUERADE
        ```
    3. #### Restart `dnsmasq`:
        ```bash
        sudo systemctl restart dnsmasq
        ```
    Now you should be able to connect to the AP and use its internet connection to access the internet. (If you have a working internet connection on its client side)

11. ### Automate the workaround:
    1. #### Create a new file:
        ```bash
        sudo nano start-ap-managed-wifi.sh
        ```
    2. #### Add the following content:
        ```bash
        #!/bin/bash
        LOGFILE="/var/log/pi_startup.log"
        echo "[$(date)] Starting script. Sleeping 45 sec..." >> $LOGFILE
        sleep 45
        echo "[$(date)] Starting execution" >> $LOGFILE
        sudo sysctl -w net.ipv4.ip_forward=1
        echo "[$(date)] Enabled ip forwarding" >> $LOGFILE
        sudo iptables -t nat -A POSTROUTING -s 192.168.10.0/24 ! -d 192.168.10.0/24 -j MASQUERADE
        echo "[$(date)] Modified iptables to set up NAT" >> $LOGFILE
        sudo systemctl restart dnsmasq
        echo "[$(date)] Restarted dnsmasq" >> $LOGFILE
        echo " " >> $LOGFILE
        ```

    3. #### Make the script executable:
        ```bash
        sudo chmod +x start-ap-managed-wifi.sh
        ```
    4. #### Add a cronjob to run the script on boot:
        ```bash
        sudo crontab -e
        ```
        Add the following line to the end of the file:
        ```bash
        @reboot /home/pi/start-ap-managed-wifi.sh
        ```

Continue to [SCRIPT.md](./SCRIPT.md) to set up bluetooth and the script.

***Note:** These instructions are tested on Raspbian Buster.  
Shoutout to [TheWalrus](https://blog.thewalr.us/2017/09/26/raspberry-pi-zero-w-simultaneous-ap-and-managed-mode-wifi/) for the original instructions. A comment under the post pointed out that the instructions depend upon if-up and if-down system which is no longer used in Raspian Buster. You might want to visit the original post for more information.*

>These instructions depend upon if-up and if-down system used by Raspbian Stretch version.  
>
>But as of 2020, you would be using Raspbian Buster, which uses a different system, based on dhcpcd daemon. While it is technically possible to still get it working (because the ifup/ifdown system are still there), it is recommended to use systemd-networkd approach, which doesn't depend upon having to introduce udev hook.  
>
>The instructions are here: [https://raspberrypi.stackex...](https://disq.us/url?url=https%3A%2F%2Fraspberrypi.stackexchange.com%2Fquestions%2F89803%2Faccess-point-as-wifi-router-repeater-optional-with-bridge%2F89804%2389804%3AtorAhAl318HVmaNbHEe6ej2YO6s&cuid=4278722)