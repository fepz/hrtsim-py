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
            b = task.data["ss"]["Fast"]["b"]
            if (t > b) or (t <= (b - task.period)):
                a_t = ceil(t / task.period)
                task.data["ss"]["Fast"]["a"] = a_t * task.wcet
                task.data["ss"]["Fast"]["b"] = a_t * task.period
            w = w + task.data["ss"]["Fast"]["a"]
        return t - tc - w + wc, w

    def _loop(di, t1, task_list):
        t1_tmp = t1
        w = 0
        cc = 0

        for task in reversed(task_list):
            if (t1_tmp <= task.data["ss"]["Fast"]["b"] - task.period) or (
                    t1_tmp > task.data["ss"]["Fast"]["b"]):
                _ceil = ceil(t1_tmp / task.period)
                cc += 1
                ceil_a = _ceil * task.wcet
                ceil_b = _ceil * task.period

                if ceil_a > task.data["ss"]["Fast"]["a"]:
                    t1_tmp += ceil_a - task.data["ss"]["Fast"]["a"]
                    if t1_tmp > di:
                        break

                task.data["ss"]["Fast"]["a"] = ceil_a
                task.data["ss"]["Fast"]["b"] = ceil_b

            w = w + task.data["ss"]["Fast"]["a"]

        return w, t1_tmp, cc

    def _heuristic(tc, wc, tmas, tmax, smax, di, tasks, htasks):
        cc = 0
        tmin = di
        slack_calcs = 0

        remain_htasks = []

        for htask in htasks:
            a1 = htask.data["ss"]["Fast"]["a"]
            b1 = htask.data["ss"]["Fast"]["b"]

            if tmas <= (b1 - htask.period):
                a1 -= htask.wcet
                b1 -= htask.period
                htask.data["ss"]["Fast"]["a"] -= htask.wcet
                htask.data["ss"]["Fast"]["b"] -= htask.period

            if tmin > b1:
                tmin = b1

            if di > b1:
                if b1 > tmas:
                    if htask.data["ss"]["Fast"]["c"] != b1:
                        slack_tmp, slackcalc_cc = slackcalc(tasks, tc, b1, wc)
                        #points.append(b1)
                        cc += slackcalc_cc
                        slack_calcs += 1

                        if slack_tmp > smax:
                            smax = slack_tmp
                            tmax = b1
                        else:
                            if slack_tmp == smax:
                                if tmax > b1:
                                    tmax = b1

                htask.data["ss"]["Fast"]["c"] = b1
                remain_htasks.append(htask)

        return tmin, tmax, smax, remain_htasks, cc, slack_calcs

    ceil.counter = 0
    floor.counter = 0

    points = []

    # theorems and corollaries applied
    theorems = []

    xi = ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return {"slack": task.data["ss"]["di"] - tc - task.data["R"], "ttma": task.data["ss"]["di"], "cc": ceil.counter,
                "theorems": [], "interval_length": 0}

    # sort the task list by period (RM)
    tl = sorted(task_list, key=lambda x: x.period)

    kmax = task.data["k"]
    tmax = task.data["ss"]["di"]

    # immediate higher priority task
    htask = tl[task.identifier - 2]

    # corollary 5 (theorem 13) for RM
    if htask.data["ss"]["di"] + htask.wcet >= task.data["ss"]["di"] >= htask.data["ss"]["ttma"]:
        return {"slack": htask.data["ss"]["slack"] - task.wcet, "ttma": htask.data["ss"]["ttma"], "cc": ceil.counter,
                "theorems": [5], "interval_length": 0}

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
    k2, slackcalc_cc = slackcalc(tl[:task.identifier], tc, task.data["ss"]["di"], wc)
    slack_calcs = 1
    points.append(task.data["ss"]["di"])

    if k2 >= kmax:
        if k2 == kmax:
            if tmax > task.data["ss"]["di"]:
                tmax = task.data["ss"]["di"]
        else:
            tmax = task.data["ss"]["di"]
        kmax = k2

    # slack at the deadline
    s = kmax

    t1 = t = interval

    # higher priority tasks
    htl = tl[:task.identifier - 1]
    for htask in htl:
        htask.data["ss"]["Fast"]["c"] = 0

    # epsilon
    e = 5 * 0.0000001

    # iterative section
    while task.data["ss"]["di"] > t:
        w, t1, loop_cc = _loop(task.data["ss"]["di"], t1, tl[:task.identifier])

        if t1 > task.data["ss"]["di"]:
            break

        tmas = tc + s + w - wc

        if t == tmas:
            if tmax == tmas:
                # fixed point previously found
                t += e
                s += e
            else:
                # new fixed point
                if tmax > tmas:
                    tmax = tmas

                # heuristic
                tmin, tmax, s, htl, heuristic_cc, heuristic_slack_calcs = _heuristic(tc, wc, tmas, tmax, kmax, task.data["ss"]["di"], tl[:task.identifier], htl)
                slack_calcs += heuristic_slack_calcs

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
            "interval_length": task.data["ss"]["di"] - interval}
