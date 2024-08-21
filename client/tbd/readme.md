# Installation
1. Clone the Repository

    ```bash
    sudo git clone https://github.com/infinitel8p/Security-Cam.git /opt/security-cam
    ``` 

    sudo apt install nodejs
    sudo apt install npm


2. Create the Service File
    ```bash
    sudo nano /etc/systemd/system/security-cam.service
    ```

    Add the following to the file:

    ```shell
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
    ```

3. Reload the systemd manager configuration: `sudo systemctl daemon-reload`

4. Enable the service to start on boot: `sudo systemctl enable security-cam.service`

5. Start the service: `sudo systemctl start security-cam.service`

6. Check the status of the service: `sudo systemctl status security-cam.service`