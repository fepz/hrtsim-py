from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
from math import ceil
import sys


def rta(rts):
    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    schedulable = True

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    print("Task {}\n\tR={}".format(1, wcrt[0]))

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        print("Task {}\n\tt = {} + {} = {}".format(idx+1, wcrt[idx-1], task["C"], t_mas))

        while schedulable:
            t = t_mas
            w = task["C"]

            loops[idx] += 1
            while_loops[idx] += 1

            summation = []

            for jdx, jtask in enumerate(rts[:idx]):
                loops[idx] += 1
                for_loops[idx] += 1

                w += ceil(t_mas / jtask["T"]) * jtask["C"]

                ceils[idx] += 1

                summation.append((t_mas, jtask["T"], jtask["C"]))

                if w > task["D"]:
                    schedulable = False
                    break

            print("\tt = {} + {} = {}".format(task["C"], " + ".join(["[{}/{}]*{}".format(t, p, c) for t, p, c in summation]), w))

            t_mas = w

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    #return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops, sum(while_loops), False]
    return schedulable

def rta2(rts):
    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    print("Task {}\n\tR={}".format(1, wcrt[0]))

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        print("Task {}\n\tt = {} + {} = {}".format(idx+1, wcrt[idx-1], task["C"], t_mas))

        while schedulable:
            t = t_mas

            loops[idx] += 1
            while_loops[idx] += 1

            summation = []

            for jdx, jtask in enumerate(rts[:idx]):
                loops[idx] += 1
                for_loops[idx] += 1

                tmp = ceil(t_mas / jtask["T"])
                a_tmp = tmp * jtask["C"]

                summation.append((t_mas, jtask["T"], jtask["C"], a_tmp, a[jdx]))

                t_mas += (a_tmp - a[jdx])
                ceils[idx] += 1

                if t_mas > task["D"]:
                    schedulable = False
                    break

                a[jdx] = a_tmp

            a_strs = ["A={} → {}".format(e[4], e[3]) for e in summation]
            c_strs = ["[{}/{}]*{}".format(t, p, c) for t, p, c, _, _ in summation]
            max_a_length = len(max(a_strs))
            max_c_length = len(max(c_strs))
            print("\t         {}".format("   ".join([format(a, "^{}".format(max_c_length)) for a in a_strs])))
            print("\tt = {} + {} = {}".format(task["C"], " + ".join([format(c, "^{}".format(max_c_length)) for c in c_strs]), t_mas))

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    #return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops, sum(while_loops), False]
    return schedulable

def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Simulate a RTS.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.", default="1")
    parser.add_argument("--method", type=str, default="rta", help="Method to test")
    return parser.parse_args()


def main():
    args = get_args()

    sched_methods = {"RTA": rta,
                     "RTA2": rta2}

    try:
        for rts in get_from_file(args.file, mixrange(args.rts)):
            sched_methods[args.method](rts["ptasks"])
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
