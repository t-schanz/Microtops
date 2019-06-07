import serial
import os
import sys
import time
import logging
import numpy as np
from dateutil import parser
from serial.tools import list_ports

class MicroReader(object):
    def __init__(self, port=None, outpath="../../output/", bitrate=4800):

        if port is None:
            ports = [p for p,_,_ in list_ports.comports()]
            if len(ports) == 0:
                raise SystemError("No COM ports found. Make sure you have installed"
                                  " the right drivers. You can otherwise provide the "
                                  "name of the port to the program")
            elif len(ports) > 1:
                port_list = '\n'.join(ports)
                raise LookupError(f"More than one COM port was found. Please"
                                  f"provide the right port to the program:\n"
                                  f"{port_list}")
            else:
                self.port = ports[0]

        else:
            self.port = port
        self.bitrate = bitrate
        self.outpath = outpath
        self.data = None

    def read_microtop_data(self):
        connection = serial.Serial(self.port, timeout=1, baudrate=self.bitrate)
        logging.info("Initiated communication")
        time.sleep(1)
        connection.write("\r\n".encode())
        logging.info("Waking up device")
        menu = connection.readlines()
        connection.write("P".encode())
        self.raw_data = connection.readlines()
        connection.close()
        decode_func = np.vectorize(lambda x: x.decode().replace("\r\n","\n"))
        self.raw_data_decoded = decode_func(self.raw_data)
        self.raw_str = b"".join(self.raw_data).decode()
        self.data = np.genfromtxt(map(lambda s: s.encode('utf8'), self.raw_data_decoded),
                                delimiter=",",
                                skip_header=2,
                                skip_footer=1,
                                dtype=None,
                                names=True
                                  )

    def write_output(self):
        self.outfile = os.path.join(self.outpath, self.get_filename())
        f = open(self.outfile, 'w')
        f.writelines(self.raw_data_decoded)
        f.close()

    def get_filename(self):
        get_dates = np.vectorize(lambda x, y: parser.parse(x.decode() + " " + y.decode() + " UTC"))
        dates = get_dates(self.data["DATE"], self.data["TIME"])
        start_date = dates[0].strftime("%Y%m%d_%H%M%S")
        end_date = dates[-1].strftime("%Y%m%d_%H%M%S")

        filename = f"Microtops_{start_date}_to_{end_date}.txt"
        return filename

    def clear_data(self):
        connection = serial.Serial(self.port, timeout=1, baudrate=self.bitrate)
        logging.info("Initiated communication")
        time.sleep(1)
        connection.write("\r\n".encode())
        logging.info("Waking up device")
        menu = connection.readlines()
        connection.write("C".encode())
        safety_check = connection.readlines()
        connection.write("Y".encode())
        result =  safety_check = connection.readlines()
        logging.info("".join([x.decode().replace("\r\n","\n") for x in result]))
        connection.close()


if __name__ == '__main__':
    MTR = MicroReader()
    MTR.read_microtop_data()
    MTR.write_output()

