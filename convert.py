#!python

from typing import TextIO
from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
import sys


def format(rts: dict):
    print("{0:}".format(len(rts["ptasks"])))
    for task in rts["ptasks"]:
        print("{0:} {1:} {2:}".format(task["C"], task["T"], task["D"]))


def convert_files(file: TextIO, ids: list) -> None:
    for rts in get_from_file(file, ids):
        format(rts)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Convert from XML or JSON to TXT format.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    return parser.parse_args()


def main():
    args = get_args()

    convert_files(args.file, mixrange(args.rts))


if __name__ == '__main__':
    main()
