from bin.processing.ReadData import MicroReader
from bin.processing.hourlymean import main as process_data
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    Mr = MicroReader(outpath="./output/")
    Mr.clear_data()
