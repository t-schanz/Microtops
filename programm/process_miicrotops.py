from bin.processing.ReadData import MicroReader
from bin.processing.hourlymean import main as process_data

if __name__ == "__main__":
    Mr = MicroReader(outpath="./output/")
    Mr.read_microtop_data()
    Mr.write_output()
    save_file = Mr.outfile.replace(".txt", "_mean.txt")
    process_data("", Mr.outfile, save_file)