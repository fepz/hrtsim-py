#!python

from simulations.simslack import run_sim
from argparse import ArgumentParser, FileType
from utils import calculate_k, get_rts
from schedtests import josephp
import math
import sys


def run_single_simulation(rts, args):
    """
    Simulate an rts
    :param rts: task set
    :param args: parameters
    :return: None
    """

    # Evaluate schedulability and K values.
    rts["schedulable"] = josephp(rts["tasks"], verbose=False)
    calculate_k(rts["tasks"])

    # Required fields for slack stealing simulation.
    for task in rts["tasks"]:
        task["ss"] = {'slack': task["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0, 'last_slack': 0, 'ii': 0}

    params = {
        "rts": rts,
        "instance_count": args.instance_count,
        "ss_methods": args.ss_methods,
    }

    sim_result = run_sim(params, callback=None, sink=True, retrieve_model=True)

    if sim_result["error"]:
        print("Simulation failed: {0}".format(sim_result["error_msg"]))
        sys.exit(1)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--file", type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--scheduler", nargs=1, type=str, help="Scheduling algorithm")
    parser.add_argument("--instance-count", type=int, help="Number of task instances to simulate.")
    parser.add_argument("--ss-methods", nargs='+', type=str, help="Slack Stealing methods.")
    return parser.parse_args()


def main():
    if not len(sys.argv) > 1:
        print("Error: no arguments.", file=sys.stderr)
        sys.exit(1)

    args = get_args()

    for rts in get_rts(args.file):
        run_single_simulation(rts, args)


if __name__ == '__main__':
    main()
