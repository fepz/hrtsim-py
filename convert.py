#!python

from typing import TextIO
from argparse import ArgumentParser, FileType
import xml.etree.cElementTree as et
import sys


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


def format(rts: dict):
    print("{0:}".format(len(rts["tasks"])))
    for task in rts["tasks"]:  
        print("{0:} {1:} {2:}".format(task["C"], task["T"], task["D"]))


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--file", type=FileType('r'), help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.")
    return parser.parse_args()


def main():
    if not len(sys.argv) > 1:
        print("Error: no arguments.", file=sys.stderr)
        sys.exit()

    args = get_args()

    rts_list = mixrange(args.rts)
    for rts in get_from_file(args.file, rts_list):
        format(rts)

if __name__ == '__main__':
    main()
