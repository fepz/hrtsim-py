import xml.etree.cElementTree as et
import math

from functools import reduce
try:
    from fractions import gcd
except ImportError:
    def gcd(a, b):
        while b:
            a, b = b, a % b
        return a


def lcm(rts):
    """ Calcula el hiperperiodo de rts """
    periods = []
    for task in rts:
        periods.append(task["T"])
    return reduce(lambda x, y: (x * y) // gcd(x, y), periods, 1)


def calc_fu(rts):
    """ Calcula el FU del rts """
    fu = 0
    for task in rts:
        fu = fu + (float(task["C"]) / float(task["T"]))
    return fu


def cota_liu(rts):
    """ Calcula planificabilidad por la cota de Liu """
    return len(rts) * (pow(2, 1.0 / float(len(rts))) - 1)


def cota_bini(rts):
    """ Calcula planificabilidad por la cota de Bini """
    cota = 1
    for task in rts:
        cota *= ((float(task["C"]) / float(task["T"])) + 1)
    return cota


def joseph_wcrt(rts):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    schedulable = True
    rts[0]["R"] = rts[0]["C"]
    for i, task in enumerate(rts[1:], 1):
        r = 1
        c, t, d = task["C"], task["T"], task["D"]
        while schedulable:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp["C"], taskp["T"]
                w += math.ceil(float(r) / float(tp)) * cp
            w = c + w
            if r == w:
                break
            r = w
            if r > d:
                schedulable = False
        task["R"] = r
    return schedulable


def first_free_slot(rts):
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


def calculate_k(rts):
    """ Calcula el K de cada tarea (máximo retraso en el instante critico) """
    rts[0]["k"] = rts[0]["T"] - rts[0]["C"]

    for i, task in enumerate(rts[1:], 1):
        r = 1
        k = 1
        c, t, d = task["C"], task["T"], task["D"]
        while True:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp["C"], taskp["T"]
                w += math.ceil(float(r) / float(tp)) * cp
            w = c + w + k
            if r == w:
                r = 1
                k = k + 1
            r = w
            if r > d:
                break
        task["k"] = k - 1


def load_from_xml(file, rts_id, start=0, limit=10000):
    # iterator over the xml file
    context = et.iterparse(file, events=('start', 'end',))
    context = iter(context)
    event, root = next(context)

    size = int(float(root.get("size")))
    ntask = int(float(root.get("n")))

    current_id, rts, rts_found = 0, dict(), False

    rts["id"] = rts_id
    rts["tasks"] = []

    # read the xml, parse task-sets and simulate it
    for event, elem in context:
        if elem.tag == 'S':
            if event == 'start':
                current_id = int(float(elem.get("count")))
                if rts_id == current_id:
                    rts_found = True
            if event == 'end':
                if rts_found:
                    break
                elem.clear()

        if rts_found:
            if elem.tag == 'i':
                if event == 'start':
                    task = elem.attrib
                    for k, v in task.items():
                        task[k] = int(float(v))
                    rts["tasks"].append(task)

        root.clear()

    del context

    if rts_found:
        rts["fu"] = calc_fu(rts["tasks"])
        rts["lcm"] = lcm(rts["tasks"])
        rts["liu"] = cota_liu(rts["tasks"])
        rts["bini"] = cota_bini(rts["tasks"])
        rts["schedulable"] = joseph_wcrt(rts["tasks"])
        calculate_k(rts["tasks"])

        # Add the required fields for slack stealing simulation.
        for task in rts["tasks"]:
            task["ss"] = {'slack': task["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0, 'last_slack': 0,
                          'ii': 0}

    return rts
