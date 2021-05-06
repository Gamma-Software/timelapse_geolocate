#!/usr/bin/env python
import cv2
import numpy as np
import io
from urllib.request import urlopen, Request
from PIL import Image


def generate_map(lat, lon, id):
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

    import cartopy.io.img_tiles as cimgt

    cimgt.OSM.get_image = image_spoof  # reformat web request for street map spoofing
    osm_img = cimgt.GoogleTiles()  # spoofed, downloaded street map
    #osm_img = cimgt.QuadtreeTiles()  # spoofed, downloaded street map

    fig = plt.figure(figsize=(5,5), frameon=False)
    ax1 = plt.axes(projection=osm_img.crs)
    center_pt = [lat[-1], lon[-1]]  # lat/lon of One World Trade Center in NYC
    zoom = 0.1  # for zooming out of center point
    print(center_pt)
    extent = [center_pt[1] - (zoom * 1.5), center_pt[1] + (zoom * 1.5), center_pt[0] - zoom,
              center_pt[0] + zoom]  # adjust to zoom
    print(extent)
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
    plt.plot(lon, lat, color='red', linewidth=2, alpha=0.5,
             transform=ccrs.Geodetic(),
             )
    plt.plot(lon[-1], lat[-1],
             color='blue', markersize=10, marker='o',
             transform=ccrs.Geodetic(),
             )
    plt.savefig("map/"+str(id)+".png",bbox_inches='tight', pad_inches=0)


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

    cv2.imwrite("../data/result/"+str(id)+".png", frame)
    return frame
