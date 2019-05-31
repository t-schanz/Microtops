from bin.microtop_alarm.ImageProcessing import ImageProcessor
from bin.microtop_alarm.SendingMail import ErrorMailer
import glob
from datetime import datetime as dt
import configparser
import os
import time
import sys

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

    if (minute_counter > 15) and not status:
        os.system("( speaker-test -t sine -f 1000 )& pid=$! ; sleep 0.1s ; kill -9 $pid")
        minute_counter = 0

    time.sleep(1*60)
    minute_counter += 1
