from bin.processing.ReadData import MicroReader
from bin.processing.hourlymean import main as process_data
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', nargs="+", type=int, help="Set the input files to be processed",
                        required=True)

    args = vars(parser.parse_args())
    return args


if __name__ == "__main__":
    args = get_args()
    Mr = MicroReader(outpath="./output/")
    save_file = Mr.outfile.replace(".txt", "_mean.txt")
    for file in args["files"]:
        process_data("", file, save_file)
