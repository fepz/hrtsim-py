#!python

from simulations.simslack import run_sim
from argparse import ArgumentParser
from utils import calculate_k
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

    params = {
        "instance_cnt": args.instance_count,
        "ss_methods": args.ss_methods,
    }

    sim_result = run_sim(rts, params, callback=None, sink=True, retrieve_model=True)

    if sim_result["error"]:
        print("Simulation failed!")
        print("\t{0}".format(sim_result["error_msg"]))


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--scheduler", nargs=1, type=str, help="Scheduling algorithm")
    parser.add_argument("--instance-count", type=int, help="Number of task instances to simulate.")
    parser.add_argument("--ss-methods", nargs='+', type=str, help="Slack Stealing methods.")
    parser.add_argument("--silent", action="store_true", help="Suppress output.")
    return parser.parse_args()


def main():
    if not len(sys.argv) > 1:
        print("Error: no arguments.", file=sys.stderr)
        sys.exit()

    args = get_args()

    param_keys = ["C", "T", "D"]

    rts = {"id": 0, "tasks": []}
    flag = False
    for line in sys.stdin.readlines():
        if not flag:
            number_of_tasks = int(line)
            flag = True
            rts["tasks"] = []
            task_counter = 0
        else:
            task = {}
            number_of_tasks -= 1
            task_counter += 1
            params = line.split()
            
            for k, v in zip(param_keys, params):
                task[k] = int(v)
            task["nro"] = task_counter
            rts["tasks"].append(task)

            if number_of_tasks == 0:
                flag = False

                rts["schedulable"] = josephp(rts["tasks"], verbose=False)
                calculate_k(rts["tasks"])

                # Add the required fields for slack stealing simulation.
                for task in rts["tasks"]:
                    task["ss"] = {'slack': task["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0, 'last_slack': 0, 'ii': 0}

                run_single_simulation(rts, args)


if __name__ == '__main__':
    main()
