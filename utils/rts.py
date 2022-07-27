import math


def lcm(rts: list) -> float:
    """ Real-time system hiperperiod (l.c.m) """
    from functools import reduce
    return reduce(lambda x, y: (x * y) // math.gcd(x, y), [task["T"] for task in rts], 1)


def uf(rts: list) -> float:
    """ Real-time system utilization factor """
    return sum([float(task["C"]) / float(task["T"]) for task in rts])


def liu_bound(rts: list) -> float:
    """ Evaluate schedulability using the Liu & Layland bound """
    return len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)


def bini_bound(rts):
    """ Evaluate schedulability using the hyperbolic bound """
    from functools import reduce
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


def calculate_k(rts: list, vf=1.0) -> None:
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    rts[0]["k"] = rts[0]["T"] - (rts[0]["C"] * vf)

    for i, task in enumerate(rts[1:], 1):
        t = 0
        k = 1
        while t <= task["D"]:
            w = k + (task["C"]*vf) + sum([math.ceil(float(t) / float(taskp["T"]))*(taskp["C"]*vf) for taskp in rts[:i]])
            if t == w:
                k += 1
            t = w
        task["k"] = k - 1


def calculate_y(rts: list) -> None:
    """ Calcula el tiempo de promoción para cada tarea, para Dual Priority """
    for task in rts:
        task["y"] = task["D"] - task["R"]


def mixrange(s):
    """
    Create a list of numbers from a string. Ie: "1-3,6,8-10" into [1,2,3,6,8,9,10]
    :param s: a string
    :return: a list of numbers
    """
    r = []
    for i in s.split(','):
        if '-' not in i:
            r.append(int(i))
        else:
            l, h = map(int, i.split('-'))
            r += range(l, h+1)
    return r


def rta(rts, vf=1.0):
    from math import ceil

    schedulable = True

    t = rts[0]["C"] * vf
    rts[0]["R"] = rts[0]["C"] * vf

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + (task["C"] * vf)

        while schedulable:
            t = t_mas
            w = task["C"] * vf

            for jdx, jtask in enumerate(rts[:idx]):
                w += ceil(t_mas / jtask["T"]) * (jtask["C"] * vf)
                if w > task["D"]:
                    schedulable = False
                    break

            t_mas = w
            if t == t_mas:
                task["R"] = t
                break

        if not schedulable:
            break

    return schedulable
