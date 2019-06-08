from bin.processing.ReadData import MicroReader
from bin.processing.hourlymean import main as process_data
import argparse


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--files', nargs="+", help="Set the input files to be processed",
                        required=True)

    args = vars(parser.parse_args())
    return args


if __name__ == "__main__":
    args = get_args()
    Mr = MicroReader("", outpath="./output/")

    for file in args["files"]:
        file_ending = file.split(".")[-1]
        save_file = file.replace(f".{file_ending}", f"_mean.{file_ending}")
        process_data("", file, save_file)
