from typing import TextIO
import xml.etree.cElementTree as et
import sys

def get_from_xml(file: TextIO, rts_id_list: list) -> dict:
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
        rts = {"id": rts_id, "ptasks": []}

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
                        rts["ptasks"].append(task)

            root.clear()

        yield rts
    del context


def get_from_json(file: TextIO, ids: list) -> dict:
    """
    Retrieve the specified rts from a json file
    :param file: file object handle
    :param ids: list of rts ids
    :return: list of rts
    """

    def get_tasks(ptasks: list) -> list:
        result = []
        for nro, task in enumerate(ptasks, 1):
            if "nro" not in task:
                task["nro"] = nro
            if "C" not in task:
                task["C"] = task.pop("c")
            if "T" not in task:
                task["T"] = task.pop("t")
            if "D" not in task:
                task["D"] = task.pop("d", task["T"])
            result.append(task)
        return result

    def get_atasks(tasks: list) -> list:
        result = []
        for nro, task in enumerate(tasks, 1):
            if "nro" not in task:
                task["nro"] = nro
            if "C" not in task:
                task["C"] = task.pop("c")
            if "D" not in task:
                task["D"] = task.pop("d", 0)
            result.append(task)
        return result

    import json
    rts_in_file = json.load(file)
    rts_list = []

    for id, tasks in [(id, rts_in_file[id]) for id in ids]:
        rts = {"id": id, "ptasks": get_tasks(tasks["periodic"]), "atasks": [], "stasks": []}

        if "aperiodic" in tasks:
            rts["atasks"] = get_atasks(tasks["aperiodic"])

        rts_list.append(rts)

        yield rts


def get_from_txt(file: TextIO) -> dict:
    param_keys = ["C", "T", "D"]

    rts = {"id": 0, "tasks": []}

    flag = False

    rts_counter = 0

    for line in file.readlines():
        if not flag:
            number_of_tasks = int(line)
            flag = True
            rts_counter += 1
            rts["id"] = rts_counter
            rts["ptasks"] = []
            task_counter = 0
        else:
            task = {}
            number_of_tasks -= 1
            task_counter += 1
            params = line.split()
            
            for k, v in zip(param_keys, params):
                task[k] = int(v)
            task["nro"] = task_counter
            rts["ptasks"].append(task)

            if number_of_tasks == 0:
                flag = False

                yield rts


def get_from_file(file: TextIO, ids: list = []) -> dict:
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
    if file_type == '.txt':
        return get_from_txt(file)
    else:
        return get_from_txt(file)

