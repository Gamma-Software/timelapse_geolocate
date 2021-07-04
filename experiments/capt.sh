# https://ffmpeg.org/ffmpeg.html#Synopsis
ffmpeg -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -rtsp_transport tcp image%03d.jpg
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -frames:v image%03d.jpg
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" image%03d.jpg

# The one
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -vf fps=1  image%03d.jpg

# Add timestamp
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -vf fps=1 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"

# Get better jpg quality
ffmpeg -rtsp_transport tcp -y -i "rtsp://admin:pam1249CS1110ragot&@192.168.1.23:554//h264Preview_01_main" -q:v 4 -vf fps=1 -strftime 1 "%Y-%m-%d_%H-%M-%S.jpg"
