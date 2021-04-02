import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
import cartopy.io.img_tiles as cimgt
import io
from urllib.request import urlopen, Request
from PIL import Image

def show_map(lat, lon, id):
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
    #osm_img = cimgt.GoogleTiles()  # spoofed, downloaded street map
    osm_img = cimgt.QuadtreeTiles()  # spoofed, downloaded street map

    fig = plt.figure(figsize=(12, 9))  # open matplotlib figure
    ax1 = plt.axes(projection=osm_img.crs)  # project using coordinate reference system (CRS) of street map
    center_pt = [lat[-1], lon[-1]]  # lat/lon of One World Trade Center in NYC
    zoom = 0.01  # for zooming out of center point
    print(center_pt)
    extent = [center_pt[1] - (zoom * 2.0), center_pt[1] + (zoom * 2.0), center_pt[0] - zoom,
              center_pt[0] + zoom]  # adjust to zoom
    ax1.set_extent(extent)  # set extents

    scale = np.ceil(-np.sqrt(2) * np.log(np.divide(zoom, 350.0)))  # empirical solve for scale based on zoom
    scale = (scale < 20) and scale or 19  # scale cannot be larger than 19
    ax1.add_image(osm_img, int(scale))  # add OSM with zoom specification
    # NOTE: zoom specifications should be selected based on extent:
    # -- 2     = coarse image, select for worldwide or continental scales
    # -- 4-6   = medium coarseness, select for countries and larger states
    # -- 6-10  = medium fineness, select for smaller states, regions, and cities
    # -- 10-12 = fine image, select for city boundaries and zip codes
    # -- 14+   = extremely fine image, select for roads, blocks, buildings
    plt.plot(lon, lat, color='red', linewidth=2, marker='o', alpha=0.5,
             transform=ccrs.Geodetic(),
             )
    plt.plot(lon[-1], lat[-1],
             color='blue', markersize=10, marker='^',
             transform=ccrs.Geodetic(),
             )
    plt.savefig("figure"+str(id)+".png")
    #plt.show()
    plt.close()


lat_file = open('../data/lat.txt', 'r')
lon_file = open('../data/lon.txt', 'r')
lat_lines = lat_file.readlines()
lon_lines = lon_file.readlines()
lat_list = []
lon_list = []
for lat, lon in zip(lat_lines, lon_lines) :
    lat_list.append(float(lat.strip('\n')))
    lon_list.append(float(lon.strip('\n')))
    show_map(lat_list, lon_list, len(lat_list))
lat_file.close()
lon_file.close()
