#!/bin/bash
/usr/bin/rpicam-vid -t 0 -n --width 1296 --height 972 --framerate 40 --codec h264 --bitrate 1000000 --inline -o - | ffmpeg -re -i - -c copy -f rtsp rtsp://localhost:8554/mystream


#/usr/bin/libcamera-vid -t 0 -n --width 1296 --height 972 \
#  --framerate 40 --codec h264 --bitrate 1000000 --inline -o - | \
#ffmpeg -re -i - -vf "vflip" -c:v libx264 -preset ultrafast -tune zerolatency \
#-f rtsp rtsp://localhost:8554/mystream
