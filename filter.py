#!python
from argparse import ArgumentParser, FileType
from utils.rts import calculate_k, mixrange
from utils.files import get_from_file
from schedtests import josephp
import sys


def format(rts: dict):
    print("{0:}".format(len(rts["ptasks"])))
    for task in rts["ptasks"]:
        print("{0:} {1:} {2:}".format(task["C"], task["T"], task["D"]))


def filter(args, rts: dict):
    rts["schedulable"] = josephp(rts["ptasks"])[0]
    if args.sched:
        if rts["schedulable"]:
            format(rts)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Filter RTS from file.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--sched", action="store_true", default=True, help="Scheduling algorithm")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    return parser.parse_args()


def main():
    args = get_args()

    try:
        for rts in get_from_file(args.file, mixrange(args.rts)):
            filter(args, rts)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
