import xml.etree.cElementTree as et


def load_from_xml(file, rts_id, start=0, limit=10000):
    # iterator over the xml file
    context = et.iterparse(file, events=('start', 'end',))
    context = iter(context)
    event, root = next(context)

    size = int(float(root.get("size")))
    ntask = int(float(root.get("n")))

    current_id, rts, rts_found = 0, [], False

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
                    rts.append(task)

        root.clear()

    del context

    return rts