from typing import TextIO
from functools import reduce
import xml.etree.cElementTree as et
import math


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


def joseph_wcrt(rts: list):
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


def analyze_rts(rts: dict):
    """
    Analyze the RTS and complete fields
    :param rts: rts
    :return: None
    """
    rts["fu"] = uf(rts["tasks"])
    rts["lcm"] = lcm(rts["tasks"])
    rts["liu"] = liu_bound(rts["tasks"])
    rts["bini"] = bini_bound(rts["tasks"])
    rts["schedulable"] = joseph_wcrt(rts["tasks"])
    calculate_k(rts["tasks"])

    # Add the required fields for slack stealing simulation.
    for task in rts["tasks"]:
        task["ss"] = {'slack': task["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0, 'last_slack': 0, 'ii': 0}


def get_from_xml(file: TextIO, rts_id_list: list):
    """
    Retrieve the specified rts from a xml file
    :param file: file object handle
    :param rts_id: rts id
    :return: rts
    """
    # get an iterable
    context = et.iterparse(file.name, events=('start', 'end',))
    # turn it into a iterator
    context = iter(context)
    # get the root element
    event, root = next(context)

    current_id, rts_found = 0, False

    for rts_id in rts_id_list:
        rts = {"id": rts_id, "tasks": []}

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

        analyze_rts(rts)
        yield rts
    del context


def get_from_json(file: TextIO, ids: list) -> list:
    """
    Retrieve the specified rts from a json file
    :param file: file object handle
    :param ids: list of rts ids
    :return: list of rts
    """
    import json
    rts_in_file = json.load(file)
    rts_list = []

    for id, tasks in [(id, rts_in_file[id]) for id in ids]:
        rts = {"id": id, "tasks": []}

        # Add expected keys
        if type(tasks) is list:
            for nro, task in enumerate(tasks, 1):
                if "nro" not in task:
                    task["nro"] = nro
                if "C" not in task:
                    task["C"] = task.pop("c")
                if "T" not in task:
                    task["T"] = task.pop("t")
                if "D" not in task:
                    task["D"] = task.pop("d", task["T"])
                rts["tasks"].append(task)

        analyze_rts(rts)
        rts_list.append(rts)

        yield rts


def get_from_file(file: TextIO, ids: list):
    """
    Retrieve the specified rts from file.
    :param file: an object file
    :param ids: list of rts ids
    :return: a list with the specified rts
    """
    import os
    file_type = os.path.splitext(file.name)[1]
    if file_type == '.xml':
        return get_from_xml(file, ids)
    if file_type == '.json':
        return get_from_json(file, ids)
