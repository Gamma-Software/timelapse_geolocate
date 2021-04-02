#!/usr/bin/env python
import cv2
import numpy as np
from matplotlib import pyplot as plt
from datetime import datetime
from os import walk


def combine(map_path, frame_path, id):
    x_offset = y_offset = 20
    map_image = cv2.imread(map_path)
    scale_percent = 80
    width = int(map_image.shape[1] * scale_percent / 100)
    height = int(map_image.shape[0] * scale_percent / 100)
    dsize = (width, height)
    map_image = cv2.resize(map_image, dsize)

    frame = cv2.imread(frame_path)
    mask = np.zeros(frame.shape[:2], dtype="uint8")
    cv2.circle(mask, (frame.shape[1] - int(map_image.shape[0]/2) - x_offset,
                      frame.shape[0] - int(map_image.shape[1]/2) - y_offset),
               int(map_image.shape[0]/2), 255, -1)
    mask_inv = cv2.bitwise_not(mask)
    frame_masked = cv2.bitwise_and(frame, frame, mask=mask_inv)

    frame[frame.shape[0] - map_image.shape[0] - y_offset*2 : frame.shape[0] - y_offset*2,
          frame.shape[1] - map_image.shape[1] - x_offset : frame.shape[1] - x_offset] = map_image
    map_masked = cv2.bitwise_and(frame, frame, mask=mask)
    dst = cv2.add(frame_masked, map_masked)
    frame[0:frame.shape[0], 0:frame.shape[1]] = dst

    date = datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
    lat = 10
    lon = 15
    localisation = " lat: " + str(lat) + ", " + "lon :" + str(lon)
    text = date + ", " + localisation
    cv2.putText(frame,text,(10,30), cv2.FONT_HERSHEY_DUPLEX, 1,(0,0,0),2,cv2.LINE_AA)
    cv2.imwrite("../data/result/"+str(id)+".png", frame)


for id in range(0, 39):
    combine("../data/map/"+str(id)+".png", "../data/ggstrw/"+str(id)+".png", id)
