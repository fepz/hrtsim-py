#!python
from argparse import ArgumentParser
from utils import calculate_k
from schedtests import josephp
import sys


def format(rts: dict):
    print("{0:}".format(len(rts["tasks"])))
    for task in rts["tasks"]:  
        print("{0:} {1:} {2:}".format(task["C"], task["T"], task["D"]))


def filter(args, rts: dict):
    if args.sched:
        if rts["schedulable"]:
            format(rts)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--sched", action="store_true", default=True, help="Scheduling algorithm")
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
                filter(args, rts)


if __name__ == '__main__':
    main()
