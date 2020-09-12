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

    def slackcalc(task_list, tc, t, wc):
        w = 0
        for task in task_list:
            b = task.data["ss"]["Fixed2"]["b"]
            if (t > b) or (t <= (b - task.period)):
                a_t = ceil(t / task.period)
                task.data["ss"]["Fixed2"]["a"] = a_t * task.wcet
                task.data["ss"]["Fixed2"]["b"] = a_t * task.period
            w = w + task.data["ss"]["Fixed2"]["a"]
        return t - tc - w + wc, w

    ceil.counter = 0
    floor.counter = 0

    slack_calcs = 0
    points = []

    xi = ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return task.data["ss"]["di"] - tc - task.data["R"], task.data["ss"]["di"], ceil.counter, 0  # , []

    # sort the task list by period (RM)
    tl = sorted(task_list, key=lambda x: x.period)

    kmax = 0
    tmax = task.data["ss"]["di"]

    # immediate higher priority task
    htask = tl[task.identifier - 2]

    # corollary 2
    if (htask.data["ss"]["di"] + htask.wcet >= task.data["ss"]["di"]) and (task.data["ss"]["di"] >= htask.data["ss"]["ttma"]):
        tmax = htask.data["ss"]["ttma"]
        kmax = htask.data["ss"]["slack"] - task.wcet
        return kmax, tmax, ceil.counter, 0  # , []

    # theorem 3
    intervalo = xi + (task.deadline - task.data["R"]) + task.wcet

    # corollary 1 (theorem 4)
    if intervalo <= (htask.data["ss"]["di"] + htask.wcet) <= task.data["ss"]["di"]:
        intervalo = htask.data["ss"]["di"] + htask.wcet
        tmax = htask.data["ss"]["ttma"]
        kmax = htask.data["ss"]["slack"] - task.wcet

    # workload at t
    wc = 0
    for task in tl[:task.identifier]:
        a = floor(tc / task.deadline)
        wc += (a * task.wcet) + (task.job.actual_computation_time if task.job else 0)

    # calculate slack in deadline
    k2, w = slackcalc(tl[:task.identifier], tc, task.data["ss"]["di"], wc)
    slack_calcs += 1
    points = [task.data["ss"]["di"]]

    # update kmax and tmax if the slack at the deadline is bigger
    if k2 >= kmax:
        if k2 == kmax:
            if tmax > task.data["ss"]["di"]:
                tmax = task.data["ss"]["di"]
        else:
            tmax = task.data["ss"]["di"]
        kmax = k2

    slack_points = [(task.data["ss"]["di"], k2, w)]

    # calculate slack at arrival time of higher priority tasks
    for htask in tl[:(task.identifier - 1)]:
        ii = ceil(intervalo / htask.period) * htask.period

        while ii < task.data["ss"]["di"]:
            k2, w = slackcalc(tl[:task.identifier], tc, ii, wc)
            slack_calcs += 1
            points.append(ii)
            slack_points.append((ii, k2, w))

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

    result = {"smax": kmax, "tmax": tmax, "inv": ceil.counter + floor.counter, "slack_calcs": slack_calcs}

    return kmax, tmax, ceil.counter + floor.counter, slack_calcs  # , slack_points
    #return result