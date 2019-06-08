from bin.processing.ReadData import MicroReader
from bin.processing.hourlymean import main as process_data
import logging

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.info("Establishing connection...")
    Mr = MicroReader(outpath="./output/")
    logging.info("Reading Data...")
    Mr.read_microtop_data()
    logging.info("Writing Data...")
    Mr.write_output()
    logging.info("Creating hourly means...")
    save_file = Mr.outfile.replace(".txt", "_mean.txt")
    process_data("", Mr.outfile, save_file)
