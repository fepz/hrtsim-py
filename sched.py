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


def first_free_slot(rts: list):
    """ Calcula primer instante que contiene un slot libre por subsistema """
    free = [0] * len(rts)
    for i, task in enumerate(rts, 0):
        r = 1
        while True:
            w = 0
            for taskp in rts[:i + 1]:
                c, t = taskp[0], taskp[1]
                w += math.ceil(float(r) / float(t)) * float(c)
            w = w + 1
            if r == w:
                break
            r = w
        free[i] = r
    return free


def calculate_k(rts: list) -> None:
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    rts[0]["k"] = rts[0]["T"] - rts[0]["C"]

    for i, task in enumerate(rts[1:], 1):
        t = 0
        k = 1
        while t <= task["D"]:
            w = k + task["C"] + sum([math.ceil(float(t) / float(taskp["T"]))*taskp["C"] for taskp in rts[:i]])
            if t == w:
                k += 1
            t = w
        task["k"] = k - 1


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
