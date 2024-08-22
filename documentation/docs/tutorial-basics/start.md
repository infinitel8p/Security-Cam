---
sidebar_position: 1
---

# Start with Security-Cam

Now that you have set up your Raspberry Pi, you can start with the Security-Cam project.

## Installation

Clone the Repository

```bash
sudo git clone https://github.com/infinitel8p/Security-Cam.git /opt/security-cam
``` 

Install Node.js and npm

```bash
sudo apt install nodejs
sudo apt install npm
```

## Setup

Create the Service File

```bash 
sudo bash -c 'cat <<EOF > /etc/systemd/system/security-cam.service
[Unit]
Description=Security Cam Flask and Node.js Servers
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/opt/security-cam
ExecStart=sudo chmod +x /opt/security-cam/start.sh && sudo /opt/security-cam/start.sh
Restart=on-failure

[Install]
WantedBy=multi-user.target
EOF'
```

Reload the systemd manager configuration

```bash
sudo systemctl daemon-reload
```

Enable the service to start on boot

```bash
sudo systemctl enable security-cam.service
```

Start the service

```bash
sudo systemctl start security-cam.service
```

Check the status of the service

```bash
sudo systemctl status security-cam.service
```

You should now be able to access the Security-Cam web interface by navigating to `http://<raspberry-pi-ip>:5000` in your web browser.

The ip address of your Raspberry Pi can vary. If you are connected to the Raspberry Pi's AP and you have followed the instructions on how to set it up, you can access the web interface by navigating to `http://192.168.10.1:5000` in your web browser. If you are connected to the same network as the Raspberry Pi, you can find the ip address by running `hostname -I` on the Raspberry Pi.