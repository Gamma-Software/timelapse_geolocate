#!/usr/bin/env python3
import cv2

""" See the README.md to understand the script
"""

"""
__author__ = "Valentin Rudloff <valentin.rudloff.perso@gmail.com>"
__date__ = "30/03/2021"
__credits__ = "None for now"
"""


def combine_frame_geolocation(frame, map_image):
    """
        Combine the current a frame coming from the the camera with an image of the vehicle located on the map
        (note: we take in reference of size the frame size)
        frame: This is the opencv frame
        map_image: This is the map image to combine with the frame
        result: A combination of the frame and the map_image
    """
    # I want to put logo on top-left corner, So I create a ROI
    rows, cols, channels = frame.shape
    roi = map_image[0:rows, 0:cols]

    # Now create a mask of logo and create its inverse mask also
    img2gray = cv2.cvtColor(map_image, cv2.COLOR_BGR2GRAY)
    ret, mask = cv2.threshold(img2gray, 10, 255, cv2.THRESH_BINARY)
    mask_inv = cv2.bitwise_not(mask)

    # Now black-out the area of logo in ROI
    img1_bg = cv2.bitwise_and(roi, roi, mask=mask_inv)

    # Take only region of logo from logo image.
    img2_fg = cv2.bitwise_and(map_image, map_image, mask=mask)
    # Put logo in ROI and modify the main image
    dst = cv2.add(img1_bg, img2_fg)
    cv2.imshow('1', img2gray)
    #cv2.imshow('2', img2_fg)
    frame[0:rows, 0:cols] = dst

    #cv2.imshow('res', frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def main():
    frame = cv2.imread('data/input_image_road.jpg')
    map_image = cv2.imread('data/map.png')
    location = (48.945168, 2.095222)

    combine_frame_geolocation(frame, map_image)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    main()
