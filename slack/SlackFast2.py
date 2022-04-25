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

    @cc_counter
    def slackcalc(tasks, tc, t, wc):
        w = 0
        for task in tasks:
            tss = task.data["ss"]["Fast2"]
            b = tss["b"]
            if (t <= (b - task.period)) or (b < t):
                a_t = ceil(t / task.period)
                tss["a"] = a_t * task.wcet
                tss["b"] = a_t * task.period
            w = w + tss["a"]
        return t - tc - w + wc

    def _loop(di, t1, tasks):
        t1_tmp = t1
        w = 0

        for task in reversed(tasks):
            tss = task.data["ss"]["Fast2"]
            if (t1_tmp <= tss["b"] - task.period) or (tss["b"] < t1_tmp):
                _ceil = ceil(t1_tmp / task.period)
                ceil_a = _ceil * task.wcet
                ceil_b = _ceil * task.period

                if ceil_a > tss["a"]:
                    t1_tmp += ceil_a - tss["a"]
                    if t1_tmp > di:
                        break

                tss["a"] = ceil_a
                tss["b"] = ceil_b

            w = w + tss["a"]

        return w, t1_tmp

    def _heuristic(tc, wc, tmas, tmax, smax, tasks):
        di = tasks[-1].data["ss"]["di"]
        
        tmin = di

        points = []

        #htasks = [task for task in tasks[:-1] if task.data["ss"]["Fast2"]["b"] < di]

        for task in tasks[:-1]:
            tss = task.data["ss"]["Fast2"]
            b = tss["b"]

            if tmas <= (b - task.period):
                tss["a"] -= task.wcet
                tss["b"] -= task.period
                b = tss["b"]

            if b < tmin:
                tmin = b

            if tmas <= b < di:
                if tss["c"] != b:
                    slack_tmp = slackcalc(tasks, tc, b, wc)
                    points.append(b)

                    if slack_tmp > smax:
                        smax = slack_tmp
                        tmax = b
                    else:
                        if slack_tmp == smax:
                            if tmax > b:
                                tmax = b

                    tss["c"] = b

        return tmin, tmax, smax, points

    # collects the instants at which the slack is calculated
    ss_points = []

    # theorems and corollaries applied
    theorems = []

    xi = ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return {"slack": task.data["ss"]["di"] - tc - task.data["R"], "ttma": task.data["ss"]["di"], "cc": ceil.counter,
                "theorems": [], "interval_length": 0, "slack_calcs": 0, "points": [], "interval": 0}

    # sort the task list by period (RM)
    tl = sorted(task_list, key=lambda x: x.period)

    kmax = task.data["k"]
    tmax = task.data["ss"]["di"]

    # immediate higher priority task
    htask = tl[task.identifier - 2]

    # corollary 5 (theorem 13) for RM
    if htask.data["ss"]["di"] + htask.wcet >= task.data["ss"]["di"] >= htask.data["ss"]["ttma"]:
        return {"slack": htask.data["ss"]["slack"] - task.wcet, "ttma": htask.data["ss"]["ttma"], "cc": ceil.counter,
                "theorems": [5], "interval_length": 0, "slack_calcs": 0, "points": [], "interval": 0}

    # theorem 10
    interval = task.data["ss"]["di"] - task.data["R"] + task.wcet

    # workload at tc
    wc = 0
    for task in tl[:task.identifier]:
        a = floor(tc / task.deadline)
        wc += (a * task.wcet) + (task.job.actual_computation_time if task.job else 0)

    # corollary 4 (theorem 12) for RM
    if interval <= (htask.data["ss"]["di"] + htask.wcet) < task.data["ss"]["di"]:
        interval = htask.data["ss"]["di"] + htask.wcet

        # new initial values for kmax and tmax
        if kmax < htask.data["ss"]["slack"] - task.wcet:
            kmax = htask.data["ss"]["slack"] - task.wcet
            tmax = htask.data["ss"]["ttma"]

        theorems.append(12)

    # calculate slack in deadline
    s = slackcalc(tl[:task.identifier], tc, task.data["ss"]["di"], wc)
    ss_points.append(task.data["ss"]["di"])

    if s >= kmax:
        if s == kmax:
            if tmax > task.data["ss"]["di"]:
                tmax = task.data["ss"]["di"]
        else:
            tmax = task.data["ss"]["di"]
        kmax = s

    # use the max slack as initial value
    s = kmax

    t1 = t = interval

    # higher priority tasks
    for htask in tl[:task.identifier - 1]:
        htask.data["ss"]["Fast2"]["c"] = 0

    # epsilon
    e = 5 * 0.0000001

    # iterative section
    while t < task.data["ss"]["di"]:
        w, t1 = _loop(task.data["ss"]["di"], t1, tl[:task.identifier])

        if t1 > task.data["ss"]["di"]:
            break

        tmas = tc + s + w - wc

        if t == tmas:
            if tmax == tmas:
                # fixed point previously found
                t += e
                s += e
            else:
                # this is a new fixed point
                if tmax > tmas:
                    tmax = tmas

                tmax_arg = tmax
                tmin, tmax, s, points = _heuristic(tc, wc, tmas, tmax, kmax, tl[:task.identifier])
                #print("{0:}\tFast2\t{1:} {2:} {3:} {4:} = _heuristic(tc, wc, tmas, tmax={5:}, kmax, tasks)".format(task.job.name, tmin, tmax, s, points, tmax_arg))
                ss_points.extend(points)

                kmax = s

                if t == tmax:
                    s += e

                t = tmin + e

            t1 = t
        else:
            if t > tmas:
                s += t - tmas
            else:
                if tmas > t1:
                    t1 = tmas
                t = tmas

    return {"slack": kmax, "ttma": tmax, "cc": ceil.counter + floor.counter, "theorems": theorems,
            "interval_length": task.data["ss"]["di"] - interval, "interval": interval, 
            "slack_calcs": slackcalc.counter, "points": ss_points}
