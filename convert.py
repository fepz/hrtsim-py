#!python

from typing import TextIO
from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
import xml.etree.cElementTree as et
import sys


def format(rts: dict):
    print("{0:}".format(len(rts["tasks"])))
    for task in rts["tasks"]:  
        print("{0:} {1:} {2:}".format(task["C"], task["T"], task["D"]))


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--file", type=FileType('r'), help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.")
    return parser.parse_args()


def main():
    if len(sys.argv) == 1:
        print("Error: no arguments.", file=sys.stderr)
        sys.exit(1)

    args = get_args()

    rts_list = mixrange(args.rts)
    for rts in get_from_file(args.file, rts_list):
        format(rts)

if __name__ == '__main__':
    main()
