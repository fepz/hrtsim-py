import math

from slack.SlackUtils import _workload
from slack.SlackUtils import _slackcalc2


class SlackFixed():

    def __init__(self):
        self.method_name = "Fixed2"
        self.points = []

    def get_slack(self, task, task_list, tc):
        slack_cc = 0
        slack_calcs = 0

        xi = math.ceil(tc / task.period) * task.period
        task.data["di"] = xi + task.deadline
        slack_cc += 1

        # if it is the max priority task, the slack is trivial
        if task.identifier == 1:
            return task.data["di"] - tc - task.data["wcrt"], task.data["di"], slack_cc, 0# , []

        # sort the task list by period (RM)
        tl = sorted(task_list, key=lambda x: x.period)

        kmax = 0
        tmax = task.data["di"]

        # immediate higher priority task
        htask = tl[task.identifier - 2]

        # corollary 2
        if (htask.data["di"] + htask.wcet >= task.data["di"]) and (task.data["di"] >= htask.data["ttma"]):
            tmax = htask.data["ttma"]
            kmax = htask.data["slack"] - task.wcet
            return kmax, tmax, slack_cc, 0# , []

        # theorem 3
        intervalo = xi + (task.deadline - task.data["wcrt"]) + task.wcet

        # corollary 1 (theorem 4)
        if intervalo <= (htask.data["di"] + htask.wcet) <= task.data["di"]:
            intervalo = htask.data["di"] + htask.wcet
            tmax = htask.data["ttma"]
            kmax = htask.data["slack"] - task.wcet

        # workload at t
        wc, workload_cc = _workload(tl[:task.identifier], tc)
        slack_cc += workload_cc

        # calculate slack in deadline
        k2, slackcalc_cc, w = _slackcalc2(self.method_name, tl[:task.identifier], tc, task.data["di"], wc)
        slack_cc += slackcalc_cc
        slack_calcs += 1
        self.points = [task.data["di"]]

        # update kmax and tmax if the slack at the deadline is bigger
        if k2 >= kmax:
            if k2 == kmax:
                if tmax > task.data["di"]:
                    tmax = task.data["di"]
            else:
                tmax = task.data["di"]
            kmax = k2

        slack_points = [(task.data["di"], k2, w)]

        # calculate slack at arrival time of higher priority tasks
        for htask in tl[:(task.identifier - 1)]:
            ii = math.ceil(intervalo / htask.period) * htask.period
            slack_cc += 1

            while ii < task.data["di"]:
                k2, slackcalc_cc, w = _slackcalc2(self.method_name, tl[:task.identifier], tc, ii, wc)
                slack_cc += slackcalc_cc
                slack_calcs += 1
                self.points.append(ii)
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

        return kmax, tmax, slack_cc, slack_calcs#, slack_points
