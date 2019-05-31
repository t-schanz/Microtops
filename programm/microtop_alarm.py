from bin.microtop_alarm.ImageProcessing import ImageProcessor
import glob
from datetime import datetime as dt
import configparser
import os
import time

minute_counter = 100
here = os.path.realpath(__file__)
here = os.path.split(here)[0]
init_file = (here + "/../PATH.ini")
config = configparser.ConfigParser()
config.read(init_file)

while True:
    now = dt.utcnow()
    path = now.strftime(config["ALLSKY"]["PATH"] + "%Y/%m/%d/%H/*")
    file = sorted(glob.glob(path))[-1]

    SkImager = ImageProcessor()
    status = SkImager.get_cloudiness_status(file)

    if (minute_counter > 15) and status:
        beep = lambda x: os.system("echo -n '\a';sleep 0.2;" * x)
        beep(3)
        minute_counter = 0

    time.sleep(1*60)
    minute_counter += 1
