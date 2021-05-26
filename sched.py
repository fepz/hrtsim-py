#!python

from typing import TextIO
from argparse import ArgumentParser, FileType
from schedtests import rta, rta2, rta3, rta4, het2, josephp
from utils.files import get_from_file
from utils.rts import mixrange
import math
import sys

def analyze_rts(rts: list):
    """
    Analyze the RTS u, lcm and schedulability
    :param rts: rts
    :return: None
    """
    rta(rts)
    rta2(rts)
    rta3(rts)
    rta4(rts)
    het2(rts)
    josephp(rts)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Simulate a RTS.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    return parser.parse_args()


def main():
    args = get_args()

    try:
        print("Method\tCC")
        for rts in get_from_file(args.file, mixrange(args.rts)):
            analyze_rts(rts["tasks"])
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':
    main()
