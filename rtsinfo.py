#!python

from argparse import ArgumentParser, FileType
from schedtests import rta
from utils.files import get_from_file
from utils.rts import mixrange, uf, lcm, liu_bound, bini_bound
import sys


def print_tasks(tasks):
    """
    Print the task set into stdout without the ss field. This should use some form of filter instead of deepcopy.
    :param tasks: rts
    :return: None
    """
    from tabulate import tabulate
    import math
    # 2021: new method
    tasks[0]["ratio"] = 1
    for htask, ltask in zip(tasks[:-1], tasks[1:]):
        ltask["ratio"] = math.ceil(ltask["T"] / htask["T"])
    print(tabulate(tasks, tablefmt="github", headers="keys"))


def analyze_rts(rts: list, detail: bool):
    """
    Analyze the RTS u, lcm and schedulability
    :param rts: rts
    :return: None
    """
    print("tasks:\t{0:}".format(len(rts)))
    if detail:
        print_tasks(rts)
    print("u:\t{0:}".format(uf(rts)))
    print("lcm:\t{0:}".format(lcm(rts)))
    print("liu:\t{0:}".format(liu_bound(rts)))
    print("bini:\t{0:}".format(bini_bound(rts)))
    print("sched:\t{0:}".format(rta(rts, verbose=False)[0]))


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    parser.add_argument("--show-tasks", default=False, action="store_true", help="Show task parameters.")
    return parser.parse_args()


def main():
    args = get_args()
    try:
        for rts in get_from_file(args.file, mixrange(args.rts)):
            analyze_rts(rts["tasks"], args.show_tasks)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
