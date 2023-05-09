#!python

from typing import TextIO
from argparse import ArgumentParser, FileType
from schedtests import rta, rta_uf, rta2, rta2u, rta3, rta3u, rta3_t2_dec, rta3_t2_inc, rta3_t2_u, rta3u_asc, rta4, rta4_inc, rta4u, rta4u_p, rta4a, het2, het2u, josephp, josephp_u
from utils.files import get_from_file
from utils.rts import mixrange
import sys

sched_methods = {"RTA": rta,
                 "RTAu": rta_uf,
                 "RTA2": rta2,
                 "RTA2u": rta2u,
                 "RTA3": rta3,
                 "RTA3u": rta3u,
                 "RTA3_t2_dec": rta3_t2_dec,
                 "RTA3_t2_inc": rta3_t2_inc,
                 "RTA3_t2_u": rta3_t2_u,
                 "RTA3ua": rta3u_asc,
                 "RTA4": rta4,
                 "RTA4_inc": rta4_inc,
                 "RTA4u": rta4u,
                 "RTA4u_p": rta4u_p,
                 "RTA4a": rta4a,
                 "HET2": het2,
                 "HET2u": het2u,
                 "JYP": josephp,
                 "JYPu": josephp_u}

# [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]
result_keys = {"wcrt":  1,
               "cc":    2,
               "ceils": 3,
               "loops": 4,
               "fors":  5,
               "while": 6,
               "while_sum": 7,
               "test":  8}


def analyze_rts(rts: dict, methods: list, metric: list):
    """
    Analyze the RTS u, lcm and schedulability
    :param rts: rts
    :param methods: list of methods to test
    :param metric: list of metrics to evaluate
    :return: None
    """

    results = {}

    for method in methods if methods else sched_methods:
        results[method] = sched_methods[method](rts["ptasks"])

    for k, v in results.items():
        print("{}\t{}\t{}\t{}".format(rts["id"], k, 'T' if v[0] else 'F', "\t".join([str(v[result_keys[mk]]) for mk in metric])))

    # use ther first method scheduling result as reference
    sched = results[list(results.keys())[0]][0]
    # use the first RTA method as reference for the following RTAs
    rta_ref = None
    for k in results.keys():
        if k[:3] == "RTA":
            rta_ref = results[k]
            break

    for k, v in results.items():
        # check if the methods produces the same result
        if sched != v[0]:
            print("ERROR! schedule result {}".format(k), file=sys.stderr)
            sys.exit(1)
        # check if all rta methods produces the same wcrt
        if rta_ref and k[:3] == "RTA":
            if rta_ref[1] != v[1]:
                print("ERROR! wcrt", file=sys.stderr)
                sys.exit(1)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Simulate a RTS.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    parser.add_argument("--methods", type=str, nargs='+', default=[], help="Methods to test")
    parser.add_argument("--metric", type=str, nargs='+', default=['cc'], help="Metric")
    return parser.parse_args()


def main():
    args = get_args()

    try:
        print("ID\tMETHOD\tSCHED\t{}".format("\t".join([metric.upper() for metric in args.metric])))
        for rts in get_from_file(args.file, mixrange(args.rts)):
            analyze_rts(rts, args.methods, args.metric)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
