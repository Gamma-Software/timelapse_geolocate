
import os
import re
import shutil

def create_path(path):
    if not os.path.exists(path):
        print("Create folder", path)
        os.makedirs(path, 0o600)
        os.chown(path, 1000, 0) # Rudloff id and group Root
        os.chmod(path, 0o775) # Give all read access but Rudloff write access 

print("Configuring timelapse_trip app...")
path_to_app = "/etc/capsule/timelapse_trip"
path_to_log = "/var/log/capsule/timelapse_trip"
path_to_timelapse_tmp = "/tmp/timelapse_trip"
path_to_current_results = path_to_timelapse_tmp + "/results"
path_to_conf = "/etc/capsule/timelapse_trip/config.yaml"
path_to_conf = "/etc/capsule/timelapse_trip/config.yaml"
path_to_services = "/etc/systemd/system/timelapse_trip.service"
create_path(path_to_app)
create_path(path_to_log)
create_path(path_to_timelapse_tmp)
create_path(path_to_current_results)
if not os.path.exists(path_to_conf):
    print("Create timelapse_trip configuration")
    shutil.copy2(os.path.join(os.path.dirname(__file__), "default_config.yaml"), path_to_conf)
    os.chown(path_to_conf, 1000, 0) # Rudloff id and group Root
    os.chmod(path_to_conf, 0o775) # Give all read access but Rudloff write access
if not os.path.exists(path_to_services):
    print("Create timelapse_trip service")
    shutil.copy2(os.path.join(os.path.dirname(__file__), "timelapse_trip.service"), path_to_services)
    os.chmod(path_to_services, 0o775) # Give all read access but Rudloff write access
    os.system("systemctl daemon-reload")
    os.system("systemctl enable timelapse_trip.service")