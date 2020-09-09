import os

def load_from_file(file, ids):
    file_type = os.path.splitext(file)[1]
    if file_type == 'xml':
        from resources.xml import load_from_xml
        return load_from_xml(file, ids)
    if file_type == 'json':
        import json
        rts_in_file = json.load(file)
        for rts in [rts_in_file[i] for i in ids]:
            if type(rts) is list:
                for task in rts:
                    if "d" not in task:
                        task["d"] = task["t"]
