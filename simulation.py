#!python

from simulations.simslack import run_sim
from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import calculate_k, mixrange
from schedtests import josephp
import math
import sys


def run_simulation(rts, args):
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
        task["ss"] = {'slack': task["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 
                'last_psi': 0, 'last_slack': 0, 'ii': 0}

    params = {
        "rts": rts,
        "instance_count": args.instance_count,
        "ss_methods": args.ss_methods,
        "gantt": args.gantt
    }

    sim_result = run_sim(params)

    if sim_result["error"]:
        print("Error: RTS {0}, {1}".format(rts["id"], sim_result["error_msg"]), file=sys.stderr)
        if args.exit_on_error:
            sys.exit(1)

    if args.gantt:
        from gui.gantt import create_gantt_window
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        ex = create_gantt_window(sim_result["model"])
        return app.exec_()

    return sim_result["error"]


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Simulate a RTS.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    parser.add_argument("--scheduler", nargs=1, type=str, help="Scheduling algorithm")
    parser.add_argument("--instance-count", type=int, default=5, help="Number of task instances to simulate.")
    parser.add_argument("--ss-methods", nargs='+', type=str, help="Slack Stealing methods.")
    parser.add_argument("--gantt", action="store_true", default=False, help="Show scheduling gantt.")
    parser.add_argument("--exit-on-error", default=False, action="store_true", help="Exit if simulation error.")
    return parser.parse_args()


def main():
    args = get_args()

    try:
        error = False
        for rts in get_from_file(args.file, mixrange(args.rts)):
            error |= run_simulation(rts, args)
    except KeyboardInterrupt:
        sys.exit(1)

    if error:
        sys.exit(1)


if __name__ == '__main__':
    main()
