
def load_rts(file, ids):
    import json
    rts_in_file = json.load(file)
    for rts in [rts_in_file[i] for i in ids]:
        if type(rts) is list:
            for task in rts:
                if "d" not in task:
                    task["d"] = task["t"]
