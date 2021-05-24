#!python

from typing import TextIO
from functools import reduce
from schedtests import rta, rta2, rta3, rta4, het2, josephp
import math
import sys


def lcm(rts: list) -> float:
    """ Real-time system hiperperiod (l.c.m) """
    return reduce(lambda x, y: (x * y) // math.gcd(x, y), [task["T"] for task in rts], 1)


def uf(rts: list) -> float:
    """ Real-time system utilization factor """
    return sum([float(task["C"]) / float(task["T"]) for task in rts])


def liu_bound(rts: list) -> float:
    """ Evaluate schedulability using the Liu & Layland bound """
    return len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)


def bini_bound(rts):
    """ Evaluate schedulability using the hyperbolic bound """
    return reduce(lambda a, b: a*b, [float(task["C"]) / float(task["T"]) + 1 for task in rts])


def analyze_rts(rts: list):
    """
    Analyze the RTS u, lcm and schedulability
    :param rts: rts
    :return: None
    """
    rta(rts)
    rta2(rts)
    rta3(rts)
    rta4(rts)
    het2(rts)
    josephp(rts)


def main():
    flag = False

    param_keys = ["C", "T", "D"]

    print("Method\tCC")

    l = []
    for line in sys.stdin.readlines():
        if not flag:
            n = int(line)
            flag = True
            l = []
        else:
            task = {}
            params = line.split()
            for k, v in zip(param_keys, params):
                task[k] = int(v)
            l.append(task)
            n = n - 1
            if n == 0:
                flag = False
                analyze_rts(l)


if __name__ == '__main__':
    main()
