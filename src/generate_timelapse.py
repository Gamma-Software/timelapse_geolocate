import os
import sys
import yaml
import logging
import datetime as dt
import io
import numpy as np
import cartopy.crs as ccrs
import matplotlib.pyplot as plt
from PIL import Image
import cartopy.io.img_tiles as cimgt
from urllib.request import urlopen, Request


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


# ----------------------------------------------------------------------------------------------------------------------
# Read script parameters
# ----------------------------------------------------------------------------------------------------------------------
# path_to_conf = os.path.join("/etc/timelapse_generator/config.yaml") TODO
path_to_conf = os.path.join("../data/config.yaml")
# If the default configuration is not install, then configure w/ the default one
if not os.path.exists(path_to_conf):
    sys.exit("Configuration file %s does not exists. Please reinstall the app" % path_to_conf)
# load configuration
with open(path_to_conf, "r") as file:
    conf = yaml.load(file, Loader=yaml.FullLoader)

# ----------------------------------------------------------------------------------------------------------------------
# Initiate variables
# ----------------------------------------------------------------------------------------------------------------------
""" TODO
logging.basicConfig(
    filename="/var/log/timelapse_generator/generate_timelapse_" + dt.datetime.now().strftime("%Y%m%d-%H%M%S") + ".log",
    filemode="a",
    level=logging.DEBUG if conf["debug"] else logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
    datefmt='%m/%d/%Y %I:%M:%S %p')
"""

# Check that the process to take pictures is not running
# TODO

# Generate the maps with the gps position
#while timelapse_to_generate:
for root, dirs, _ in os.walk(conf["root_temp_image_loc"]):
    for name in dirs:
        for root, _, files in os.walk(os.path.join(root, name)):
            # Compute the list of gps_positions
            gps_positions = files.copy()
            gps_positions = list(map(lambda x: [float(y) for y in x[20:-4].split("_")], gps_positions))
            construct_gps_list = []
            # image_path_relative = os.path.join(root, name, image_path)
            for idx, image_path in enumerate(files):
                construct_gps_list.append(gps_positions[idx])
                cimgt.OSM.get_image = image_spoof  # reformat web request for street map spoofing
                osm_img = cimgt.GoogleTiles()  # spoofed, downloaded street map
                # osm_img = cimgt.QuadtreeTiles()  # spoofed, downloaded street map

                fig = plt.figure(figsize=(5, 5), frameon=False)
                ax1 = plt.axes(projection=osm_img.crs)
                zoom = 0.1  # for zooming out of center point
                extent = [construct_gps_list[idx][1] - (zoom * 1.5), construct_gps_list[idx][1] + (zoom * 1.5), construct_gps_list[idx][0] - zoom,
                          construct_gps_list[idx][0] + zoom]  # adjust to zoom
                ax1.set_extent(extent)  # set extents

                scale = np.ceil(-np.sqrt(2) * np.log(np.divide(zoom, 350.0)))  # empirical solve for scale based on zoom
                scale = (scale < 20) and scale or 19  # scale cannot be larger than 19
                ax1.add_image(osm_img, int(scale))  # add OSM with zoom specification
                ax1.set_axis_off()
                fig.add_axes(ax1)
                # NOTE: zoom specifications should be selected based on extent:
                # -- 2     = coarse image, select for worldwide or continental scales
                # -- 4-6   = medium coarseness, select for countries and larger states
                # -- 6-10  = medium fineness, select for smaller states, regions, and cities
                # -- 10-12 = fine image, select for city boundaries and zip codes
                # -- 14+   = extremely fine image, select for roads, blocks, buildings
                plt.plot(construct_gps_list, construct_gps_list, color='red', linewidth=2, alpha=0.5,
                         transform=ccrs.Geodetic(),
                         )
                plt.plot(construct_gps_list[idx][0], construct_gps_list[idx][1],
                         color='blue', markersize=10, marker='o',
                         transform=ccrs.Geodetic(),
                         )
                plt.savefig(os.path.abspath(root) + "\map_" + str(construct_gps_list[idx][0]) + "_" + str(construct_gps_list[idx][1]) +
                            ".png", bbox_inches='tight', pad_inches=0)
                print("save " + "\map_" + str(construct_gps_list[idx][0]) + "_" + str(construct_gps_list[idx][1]) + ".png")
                plt.close()
