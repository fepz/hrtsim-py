def get_slack(task, task_list, tc):
    import math

    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)

    def slackcalc(task_list, tc, t, wc):
        w = 0
        for task in task_list:
            b = task.data["ss"]["SlackHet"]["b"]
            if (t > b) or (t <= (b - task.period)):
                a_t = ceil(t / task.period)
                task.data["ss"]["SlackHet"]["a"] = a_t * task.wcet
                task.data["ss"]["SlackHet"]["b"] = a_t * task.period
            w = w + task.data["ss"]["SlackHet"]["a"]
        return t - tc - w + wc, w

    def _het_search(task_list, i, ii, params):
        method_name = "SlackHet"

        if i < 0:
            params["points"].append(ii)
            params["intervalo"] = ii  # update intervalo with the last calculated point
            return

        b = ii
        b_c = 0

        if task_list[i].data["ss"][method_name]["blimit"] <= ii:
            if task_list[i].data["ss"][method_name]["blimit"] < ii - task_list[i].period:
                b = floor(ii / task_list[i].period) * task_list[i].period
                params["cc"] += 1
            else:
                b = task_list[i].data["ss"][method_name]["blimit"]

            if b == ii:
                b_c = task_list[i].wcet

            task_list[i].data["ss"][method_name]["blimit"] = b + task_list[i].period

            if b < params["intervalo"] or b <= params["last_psi"]:
                if params["intervalo"] < b <= params["last_psi"]:
                    params["last_psi"] += task_list[i].wcet
                b = ii  # cut the b branch

        _het_search(task_list, i - 1, b, params)
        if b + task_list[i].wcet < ii:  # if b == ii, this is always false
            _het_search(task_list, i - 1, ii, params)
            params["last_psi"] = ii + task_list[i + 1].wcet
        else:
            params["last_psi"] = b + task_list[i + 1].wcet + b_c
            if b < ii:
                params["last_psi"] += task_list[i].wcet

    method_name = "SlackHet"
    params = {
        "points": [],  # t values at which slackcalc is invoked
        "slacks" : [],  # slack values calculated for each t
        "cc" : 0,
        "ss_points": [],
        "last_psi" : 0,
        "het_limit" : 0,
        "intervalo": 0,
        "minb" : 0,
        "verbose" : False  # print trace
    }

    ceil.counter = 0
    floor.counter = 0
    slack_cc = 0

    theorems = []

    slack_cc += 1
    xi = ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return {"slack": task.data["ss"]["di"] - tc - task.data["R"], "ttma": task.data["ss"]["di"], "cc": ceil.counter,
                "theorems": []}

    max_s = 0
    max_t = task.data["ss"]["di"]

    # sort the task list by period (RM)
    tl = sorted(task_list, key=lambda x: x.period)

    # immediate higher priority task
    ptask = tl[task.identifier - 2]

    # corollary 2
    if (ptask.data["ss"]["di"] + ptask.wcet >= task.data["ss"]["di"]) and (task.data["ss"]["di"] >= ptask.data["ss"]["ttma"]):
        return {"slack": ptask.data["ss"]["slack"] - task.wcet, "ttma": ptask.data["ss"]["ttma"], "cc": ceil.counter,
                "theorems": [2]}

    # theorem 3
    intervalo = xi + (task.deadline - task.data["R"]) + task.wcet

    # corollary 1 (theorem 4)
    if intervalo <= (ptask.data["ss"]["di"] + ptask.wcet) <= task.data["ss"]["di"]:
        intervalo = ptask.data["ss"]["di"] + ptask.wcet
        max_t = ptask.data["ss"]["ttma"]
        max_s = ptask.data["ss"]["slack"] - task.wcet
        theorems.append(4)

    # workload at tc
    wc = 0
    for task in tl[:task.identifier]:
        a = floor(tc / task.deadline)
        wc += (a * task.wcet) + (task.job.actual_computation_time if task.job else 0)
    slack_cc += wc

    # recursive search of points
    for tmp_task in task_list:
        tmp_task.data["ss"][method_name]["ignore"] = False
        tmp_task.data["ss"][method_name]["blimit"] = 0

    params["last_psi"] = 0
    params["cc"] = 0
    params["het_limit"] = task.data["ss"]["di"]
    params["intervalo"] = intervalo
    params["minb"] = task.data["ss"]["di"]
    _het_search(task_list[:task.identifier], task.identifier - 2, task.data["ss"]["di"], params)
    ss_points = params["points"]

    # calculate slack in each point
    for point in ss_points:
        s, s_cc = slackcalc(tl[:task.identifier], tc, point, wc)
        slack_cc += s_cc

        # update max_s and max_t
        if s > max_s:
            max_s = s
            max_t = point

    # print if points are duplicated
    import collections
    dups = [item for item, count in collections.Counter(ss_points).items() if count > 1]
    if dups:
        print(" --- Job {} , tc {},  --- ".format(task.job.name if task.job else "?", tc))
        print("dups:", dups)

    return {"slack": max_s, "ttma": max_t, "cc": ceil.counter + floor.counter, "theorems": theorems}
