import math

def get_slack(task, task_list, tc):

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

    @cc_counter
    def slackcalc(task_list, tc, t, wc):
        w = 0
        for task in task_list:
            b = task.data["ss"]["Fixed2"]["b"]
            if (t > b) or (t <= (b - task.period)):
                a_t = ceil(t / task.period)
                task.data["ss"]["Fixed2"]["a"] = a_t * task.data["C"]
                task.data["ss"]["Fixed2"]["b"] = a_t * task.period
            w = w + task.data["ss"]["Fixed2"]["a"]
        return t - tc - w + wc, w

    ceil.counter = 0
    floor.counter = 0

    # theorems and corollaries applied
    theorems = []

    xi = ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return {"slack": task.data["ss"]["di"] - tc - task.data["R"], "ttma": task.data["ss"]["di"], "cc": ceil.counter,
                "theorems": theorems, "interval_length": 0, "slack_calcs": slackcalc.counter}

    # sort the task list by period (RM)
    tl = sorted(task_list, key=lambda x: x.period)

    kmax = 0
    tmax = task.data["ss"]["di"]

    # immediate higher priority task
    htask = tl[task.identifier - 2]

    # corollary 2 (theorem 5)
    if (htask.data["ss"]["di"] + htask.data["C"] >= task.data["ss"]["di"]) and (task.data["ss"]["di"] >= htask.data["ss"]["ttma"]):
        theorems.append(5)
        return {"slack": htask.data["ss"]["slack"] - task.data["C"], "ttma": htask.data["ss"]["ttma"], "cc": ceil.counter,
                "theorems": theorems, "interval_length": 0, "slack_calcs": slackcalc.counter}

    # theorem 3
    intervalo = xi + (task.deadline - task.data["R"]) + task.data["C"]

    # corollary 1 (theorem 4)
    if intervalo <= (htask.data["ss"]["di"] + htask.data["C"]) <= task.data["ss"]["di"]:
        intervalo = htask.data["ss"]["di"] + htask.data["C"]
        tmax = htask.data["ss"]["ttma"]
        kmax = htask.data["ss"]["slack"] - task.data["C"]
        theorems.append(4)

    # workload at t
    wc = 0
    for task in tl[:task.identifier]:
        a = floor(tc / task.deadline)
        wc += (a * task.data["C"])
        if task.job and task.job.computation_time > 0:
            wc += task.data["C"]

    # calculate slack in deadline
    k2, w = slackcalc(tl[:task.identifier], tc, task.data["ss"]["di"], wc)

    # update kmax and tmax if the slack at the deadline is bigger
    if k2 >= kmax:
        if k2 == kmax:
            if tmax > task.data["ss"]["di"]:
                tmax = task.data["ss"]["di"]
        else:
            tmax = task.data["ss"]["di"]
        kmax = k2

    # calculate slack at arrival time of higher priority tasks
    for htask in tl[:(task.identifier - 1)]:
        ii = ceil(intervalo / htask.period) * htask.period

        while ii < task.data["ss"]["di"]:
            k2, w = slackcalc(tl[:task.identifier], tc, ii, wc)

            # update kmax and tmax if a greater slack value was found
            if k2 > kmax:
                tmax = ii
                kmax = k2
            else:
                if k2 == kmax:
                    if tmax > ii:
                        tmax = ii

            # next arrival
            ii += htask.period

    return {"slack": kmax, "ttma": tmax, "cc": ceil.counter + floor.counter, "theorems": theorems,
            "interval_length": task.data["ss"]["di"] - intervalo, "slack_calcs": slackcalc.counter}
