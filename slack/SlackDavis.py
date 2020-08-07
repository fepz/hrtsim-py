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

    ceil.counter = 0

    slack_cc = 0
    slack_calcs = 0
    points = []

    xi = ceil(tc / task.period) * task.period
    task.data["ss"]["di"] = xi + task.deadline
    slack_cc += 1

    # if it is the max priority task, the slack is trivial
    if task.identifier == 1:
        return task.data["ss"]["di"] - tc - task.data["R"], task.data["ss"]["di"], ceil.counter, 0  # , []

    # sort the task list by period (RM)
    tl = sorted(task_list, key=lambda x: x.period)

    # immediate higher priority task
    htasks = tl[:task.identifier]

    kdavis = task.data["k"]
    wdavis1 = xi - tc

    while wdavis1 <= (task.data["ss"]["di"] - tc):
        wdavis = wdavis1
        sum = 0

        slack_cc += len(htasks)

        for htask in htasks:
            xi1 = ceil(tc / htask.period) * htask.period - tc
            xii = wdavis - xi1
            if xii <= 0:
                techo = 0
            else:
                slack_cc += 1
                techo = ceil(xii / htask.period)
                sum = sum + htask.wcet * techo

        wdavis1 = kdavis + sum

        if wdavis == wdavis1:
            vimin = task.data["ss"]["di"] - tc - wdavis

            if vimin < 0:
                vimin = 0
            else:
                for htask in htasks:
                    slack_cc += 2
                    vi1 = ceil((wdavis - xi - tc) / htask.period)
                    if vi1 < 0:
                        vi1 = 0
                    xi1 = ceil(tc / htask.period) * htask.period - tc
                    vi = vi1 * htask.period + xi1 - wdavis
                    if vi < vimin:
                        vimin = vi
                    if vimin < 0:
                        break

            e = 1
            if vimin <= 0:
                wdavis1 += e
                kdavis += e
            else:
                kdavis += vimin
                wdavis1 += vimin
                if wdavis1 == wdavis:
                    wdavis1 += e

    return kdavis - 1, 0, ceil.counter, slack_calcs  # , slack_points
