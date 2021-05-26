from typing import TextIO
import xml.etree.cElementTree as et
import sys

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

        yield rts
    del context


def get_from_json(file: TextIO, ids: list) -> list:
    """
    Retrieve the specified rts from a json file
    :param file: file object handle
    :param ids: list of rts ids
    :return: list of rts
    """

    def get_tasks(tasks: list) -> list:
        result = []
        for nro, task in enumerate(tasks, 1):
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

    import json
    rts_in_file = json.load(file)
    rts_list = []

    for id, tasks in [(id, rts_in_file[id]) for id in ids]:
        rts = {"id": id, "tasks": [], "atasks": [], "stasks": []}

        if type(tasks["periodic"]) is list:
            rts["tasks"] = get_tasks(tasks["periodic"])

        if "aperiodic" in tasks:
            rts["atasks"] = tasks["aperiodic"]

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

