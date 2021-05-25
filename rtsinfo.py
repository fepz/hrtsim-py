#!python

from argparse import ArgumentParser
from argparse import ArgumentParser
from schedtests import rta
import utils
import sys


def print_tasks(tasks):
    """
    Print the task set into stdout without the ss field. This should use some form of filter instead of deepcopy.
    :param tasks: rts
    :return: None
    """
    from tabulate import tabulate
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
    print("u:\t{0:}".format(utils.uf(rts)))
    print("lcm:\t{0:}".format(utils.lcm(rts)))
    print("liu:\t{0:}".format(utils.liu_bound(rts)))
    print("bini:\t{0:}".format(utils.bini_bound(rts)))
    print("sched:\t{0:}".format(rta(rts, verbose=False)[0]))


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--show-tasks", default=False, action="store_true", help="Show task parameters.")
    return parser.parse_args()


def main():
    args = get_args()

    for rts in utils.get_rts(sys.stdin):
        analyze_rts(rts["tasks"], args.show_tasks)


if __name__ == '__main__':
    main()