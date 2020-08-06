import math


def get_slack(task, task_list, tc):
    from slack.SlackUtils import workload, slackcalc

    slack_cc = 0
    slack_calcs = 0

    xi = math.ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline
    slack_cc += 1

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return task.data["ss"]["di"] - tc - task.data["R"], task.data["ss"]["di"], slack_cc, 0  # , []

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
        return kmax, tmax, slack_cc, 0  # , []

    # theorem 3
    intervalo = xi + (task.deadline - task.data["R"]) + task.wcet

    # corollary 1 (theorem 4)
    if intervalo <= (htask.data["ss"]["di"] + htask.wcet) <= task.data["ss"]["di"]:
        intervalo = htask.data["ss"]["di"] + htask.wcet
        tmax = htask.data["ss"]["ttma"]
        kmax = htask.data["ss"]["slack"] - task.wcet

    # workload at t
    wc, workload_cc = workload(tl[:task.identifier], tc)
    slack_cc += workload_cc

    # New theorem.
    tmp = task.data["ss"]["di"] - task.period
    if tmp > intervalo:
        intervalo = tmp

    # calculate slack in deadline
    k2, slackcalc_cc, w = slackcalc("Fixed15", tl[:task.identifier], tc, task.data["ss"]["di"], wc)
    slack_cc += slackcalc_cc
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
        ii = math.ceil(intervalo / htask.period) * htask.period
        slack_cc += 1

        while ii < task.data["ss"]["di"]:
            k2, slackcalc_cc, w = slackcalc("Fixed15", tl[:task.identifier], tc, ii, wc)
            slack_cc += slackcalc_cc
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

    return kmax, tmax, slack_cc, slack_calcs  # , slack_points
