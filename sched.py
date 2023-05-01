#!python

from typing import TextIO
from argparse import ArgumentParser, FileType
from schedtests import rta, rta_uf, rta2, rta2u, rta3, rta3u, rta4, rta4u, rta4a, het2, het2u, josephp, josephp_u
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

    results = []

    results.append(rta(rts))
    results.append(rta_uf(rts))
    results.append(rta2(rts))
    results.append(rta2u(rts))
    results.append(rta3(rts))
    results.append(rta3u(rts))
    results.append(rta4(rts))
    results.append(rta4u(rts))
    results.append(rta4a(rts))
    het2(rts)
    het2u(rts)
    josephp(rts)
    josephp_u(rts)

    # check if all rta has the same result
    r1 = results[0][0]
    for r in results:
        if r[0] != r1:
            print("ERROR!", file=sys.stderr)
            sys.exit(1)

    # check if all rta has the same wcrt
    r1 = results[0][1]
    for r in results:
        if r[1] != r1:
            print("ERROR!", file=sys.stderr)
            sys.exit(1)



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
            analyze_rts(rts["ptasks"])
    except KeyboardInterrupt:
        sys.exit(1)

if __name__ == '__main__':
    main()
