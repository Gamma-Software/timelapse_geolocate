#!/usr/bin/env python3
import time

import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import io
from os import walk, path
import sys
from urllib.request import urlopen, Request
from PIL import Image
import argparse
import typing
import cv2

from src.ReadGPSdata import read_gps_data_log
from src.RaspCameraDriver import take_picture_annotate

""" See the README.md to understand the script
"""

"""
__author__ = "Valentin Rudloff <valentin.rudloff.perso@gmail.com>"
__date__ = "30/03/2021"
__credits__ = "None for now"
"""


def generate_map(args):
    """
        Get the current position and the last positions to create a map
        result: Generates a map displaying the gps positions (previous position in blue and current in red)
    """
    def image_spoof(self, tile):  # this function pretends not to be a Python script
        url = self._image_url(tile)  # get the url of the street map API
        req = Request(url)  # start request
        req.add_header('User-agent', 'Anaconda 3')  # add user agent to request
        fh = urlopen(req)
        im_data = io.BytesIO(fh.read())  # get image
        fh.close()  # close url
        img = Image.open(im_data)  # open image with PIL
        img = img.convert(self.desired_tile_form)  # set image format
        return img, self.tileextent(tile), 'lower'  # reformat for cartopy

    cimgt.OSM.get_image = image_spoof  # reformat web request for street map spoofing
    osm_img = cimgt.GoogleTiles()  # spoofed, downloaded street map
    # osm_img = cimgt.QuadtreeTiles()  # spoofed, downloaded street map

    fig = plt.figure(figsize=(5, 5), frameon=False)
    ax1 = plt.axes(projection=osm_img.crs)
    center_pt = [positions.lat[-1], positions.lon[-1]]  # lat/lon of One World Trade Center in NYC
    zoom = 0.1  # for zooming out of center point
    extent = [center_pt[1] - (zoom * 1.5), center_pt[1] + (zoom * 1.5), center_pt[0] - zoom,
              center_pt[0] + zoom]  # adjust to zoom
    ax1.set_extent(extent)  # set extents

    scale = np.ceil(-np.sqrt(2) * np.log(np.divide(zoom, 350.0)))  # empirical solve for scale based on zoom
    scale = (scale < 20) and scale or 19  # scale cannot be larger than 19
    ax1.add_image(osm_img, int(scale))  # add OSM with zoom specification
    ax1.set_axis_off()
    fig.add_axes(ax1)
    plt.plot(positions.lon, positions.lat, color='red', linewidth=2, alpha=0.5, transform=ccrs.Geodetic(),)
    plt.plot(positions.lon[-1], positions.lat[-1], color='blue', markersize=10, marker='o', transform=ccrs.Geodetic())
    plt.savefig("map_timestamp_" + str(timestamp) + "_lat" + str(positions.lat[-1]) + "_lon" + str(positions.lon[-1]) +
                ".png", bbox_inches='tight',
                pad_inches=0)
    plt.close()


def generate_timelapse(args):
    """
    generate_timelapse(cached_frames_folder, output_filename, framerate) -> Success/Fail
    .   @brief Generates a timelapse video with cached combined frames
    .
    .   @param cached_frames_folder this is the folder where the frames are found to
    .   @param output_filename this is the name of the video
    .   @param framerate this is the framerate of the video
    .
    .   The function/method writes the specified image to video file. It must have the same size as has
    .   been specified when opening the video writer.
    """
    # Check if the folder exists
    if not path.exists(args.cached_frames_folder):
        print("The ", args.cached_frames_folder, " does not exists")
        return False
    # Check if the framerate is correct
    if args.framerate <= 0:
        print("The framerate should be superior to 0")
        return False
    # Get the frames in cache
    _, _, cached_frames_filenames = next(walk(args.cached_frames_folder))
    frames = [cv2.imread(args.cached_frames_folder + "/" + cached_frames_filename)
              for cached_frames_filename in cached_frames_filenames]
    # Check if there are at least 2 frames to generate a timelapse
    if len(frames) < 2:
        print("There are not enough frames to generate a timelapse")
        return False
    # Check that all the frames are the same size
    if True in [frames[0].shape[:2] != frame.shape[:2] for frame in frames]:
        print("The frames size are not consistent to be combined to generate a timelapse")
        return False

    # Init the video
    video_out = cv2.VideoWriter(args.output_filename,
                                cv2.VideoWriter_fourcc(*'mp4v'),
                                args.framerate,
                                frames[0].shape[:2][::-1]) # [::-1] is needed to reverse the tuple
    # fill the video with the frames
    for frame in frames:
        video_out.write(frame)
    # Do not forget to release the video instance to pass the destroy c++ method
    video_out.release()
    print("Video output generate and saved in: " + args.output_filename)
    return True  # Timelapse generated


def take_pictures(args):
    try:
        while True:
            gps_data = read_gps_data_log()
            take_picture_annotate(args.path_to_image_folder, args.width, args.height, gps_data["latitude"], gps_data["longitude"])
            time.sleep(args.timelapse)
    except KeyboardInterrupt:
        sys.stderr.write('Ctrl-C pressed, pictures saved in '+args.path_to_image_folder)


def manual():
    print("Create a timelapse video combining photos and their gps positions (displaying the current position on a map)"
          " and the date and kilometer travelled. This project is first made for documenting a roadtrip and facilitate"
          " the sharing of the progress.")


def parse_args(cmd_args: typing.Sequence[str]):
    parser = argparse.ArgumentParser(prog='timelapseGeo')
    parser.add_argument('--version', help='Prints TimelapseGeo\'s version', action="store_true")
    subparsers = parser.add_subparsers(help='sub-command help')

    generate_parser = subparsers.add_parser('generate_map', help='Generate a map, take a photo')
    generate_parser.add_argument('localize', type=str, help='Get the gps position and generate a map with the current'
                                                            ' and past gps positions')
    generate_parser.set_defaults(func=generate_map)

    take_photo_annotate_parser = subparsers.add_parser('take_photo', help='Takes a photo with the annotation of the timestamp and location')
    take_photo_annotate_parser.add_argument('--timelapse', type=float, default=10, help='')  # Every 10 seconds
    take_photo_annotate_parser.add_argument('--width', type=int, default=3280, help='')
    take_photo_annotate_parser.add_argument('--height', type=int, default=2464, help='')
    take_photo_annotate_parser.add_argument('--path_to_image_folder', type=str, help='')
    take_photo_annotate_parser.set_defaults(func=take_pictures)

    generate_timelapse_parser = subparsers.add_parser('generate_timelapse', help="Generate a timelapse")
    generate_timelapse_parser.add_argument('--cached_frames_folder', type=str, default=".", help="Cached frame folders")
    generate_timelapse_parser.add_argument('--output_filename', type=str, default=".", help="Output filename")
    generate_timelapse_parser.add_argument('--framerate', type=float, default=10.0, help="Video framerate")
    generate_timelapse_parser.set_defaults(func=generate_timelapse)

    parser_man = subparsers.add_parser("man", help="Open timelapsegeo manual")
    parser_man.set_defaults(func=manual)

    parser.set_defaults(func=lambda x: parser.print_help())
    return parser.parse_args(args=cmd_args)


def main_args(cmd_args: typing.Sequence[str]):
    args = parse_args(cmd_args)
    sys.exit(args.func(args))


def main():
    main_args(sys.argv[1:])
    sys.exit("Incorrect configuration")
