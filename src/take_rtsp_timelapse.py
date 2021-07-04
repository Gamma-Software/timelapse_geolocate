#!/usr/bin/env python3
import time
from subprocess import Popen, PIPE




# Start taking pictures
p = Popen(['ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -q:v 4 -vf fps=1 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"'],
 stdin=PIPE, stderr=PIPE, shell=True, encoding='utf8')

p.communicate(input='q')