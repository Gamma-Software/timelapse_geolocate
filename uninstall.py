
import os
import re
import shutil
from src.path_files import *

def remove_path(path):
    if not os.path.exists(path):
        print("Create folder", path)
        os.makedirs(path, 0o740)
        os.chown(path, 1000, 1000) # Rudloff id and group Root
        os.chmod(path, 0o740) # Give all read access but Rudloff write access 

print("Uninstalling timelapse_trip app...")
if input("Want to remove config ? y/[N]").capitalize() == "Y" and os.path.exists(path_to_conf):
    print("Remove folder", path_to_conf)
    shutil.rmtree(path_to_conf)
if os.path.exists(path_to_app):
    print("Remove folder", path_to_app)
    shutil.rmtree(path_to_app)
if os.path.exists(path_to_timelapse_tmp):
    print("Remove folder", path_to_timelapse_tmp)
    shutil.rmtree(path_to_timelapse_tmp)
if os.path.exists(path_to_services):
    print("Remove timelapse_trip service")
    os.system("systemctl stop timelapse_trip.service")
    os.system("systemctl disable timelapse_trip.service")
    os.remove(path_to_services)
    os.system("systemctl daemon-reload")