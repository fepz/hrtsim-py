import math

from slack.SlackExceptions import NegativeSlackException, DifferentSlackException


def get_slack_methods():
    slack_methods = {"Fixed2": "slack.SlackFixed.SlackFixed",
                     "Fixed15":  "slack.SlackFixed15.SlackFixed15"}
    return slack_methods


def add_slack_data(rts, slack_methods):
    # Add additional parameters to each task.
    for task in rts:
        # Data required by the slack stealing methods.
        slack_data = {'slack': 0, 'wcrt': task["wcrt"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0,
                      'last_slack': 0, 'ii': 0, 'k': 0}

        # Each slack method needs its own copy of A, B, C and CC (computational cost).
        for ss_method in slack_methods:
            slack_data[ss_method.method_name] = {'a': task["C"], 'b': task["T"], 'c': 0, 'cc': []}

        task["slack_data"] = slack_data


def _workload(task_list, tc):
    w = 0
    cc = 0

    for task in task_list:
        a = math.floor(tc / task.deadline)
        w += (a * task.wcet) + (task.job.actual_computation_time if task.job else 0)
        cc += 1

    return w, cc


def _slackcalc(self, task_list, tc, t, wc):
    w = 0
    cc = 0

    for task in task_list:
        b = task.data[self.method_name]["b"]

        if (t > b) or (t <= (b - task.period)):
            a_t = math.ceil(t / task.period)
            cc += 1
            a = a_t * task.wcet
            task.data[self.method_name]["a"] = a
            task.data[self.method_name]["b"] = a_t * task.period

        w = w + task.data[self.method_name]["a"]

    return t - tc - w + wc, cc


def _slackcalc2(method_name, task_list, tc, t, wc):
    w = 0
    cc = 0

    for task in task_list:
        b = task.data[method_name]["b"]

        if (t > b) or (t <= (b - task.period)):
            a_t = math.ceil(t / task.period)
            cc += 1
            a = a_t * task.wcet
            task.data[method_name]["a"] = a
            task.data[method_name]["b"] = a_t * task.period

        w = w + task.data[method_name]["a"]

    return t - tc - w + wc, cc, w


def reduce_slacks(tasks, amount, t):
    for task in tasks:
        task.data["slack"] -= amount

        if task.data["slack"] < 0:
            raise NegativeSlackException(t, task)


def multiple_slack_calc(tc, job, tasks, slack_methods):
    slack_results = []
    #tmp_sc = []

    # calculate slack with each method in slack_methods
    for slack_method in slack_methods:
        ss_tmp, ttma_tmp, cc, slack_calcs = slack_method.get_slack(job.task, tasks, tc)
        if ss_tmp < 0:
            raise NegativeSlackException(tc, slack_method.method_name, job.name)
        slack_results.append((slack_method.method_name, ss_tmp, ttma_tmp, cc, slack_calcs))

    # verify that all the methods results are the same
    ss_ref = slack_results[0][1]
    ttma_ref = slack_results[0][2]
    for result in slack_results:
        if result[1] != ss_ref or result[2] != ttma_ref:
            raise DifferentSlackException(tc, job, result[0])

    # return slack and ttma
    return ss_ref, ttma_ref, slack_results


def _slackcalc3(self, task_list, tc, t, wc, i, w_t):
    w = 0
    cc = 0

    for task in task_list[i:]:
        b = task.data[self.method_name]["b"]

        if (t > b) or (t <= (b - task.period)):
            a_t = math.ceil(t / task.period)
            cc += 1
            a = a_t * task.wcet
            task.data[self.method_name]["a"] = a
            task.data[self.method_name]["b"] = a_t * task.period

        w = w + task.data[self.method_name]["a"]

    return t - tc - (w + w_t) + wc, cc, w + w_t


def _slackcalc4(self, task_list, tc, t, wc, mod=False, printr=False, tabs=1):
    w = 0
    cc = 0

    print_list_ceils = []  # strings for ceils operations
    print_list_abs = []  # strings for a and b values
    print_list_w = []

    for task in task_list:
        b = task.data[self.method_name]["b"]

        if (t > b) or (t <= (b - task.period)):
            if mod:
                a_t = math.ceil((t - task.data[self.method_name]["a"]) / (task.period - task.wcet))
            else:
                a_t = math.ceil(t / task.period)

            cc += 1
            a = a_t * task.wcet

            if mod:
                print_list_ceils.append(
                    "ceil( {0} / {1} )".format(t - task.data[self.method_name]["a"], task.period - task.wcet))
            else:
                print_list_ceils.append("ceil( {0} / {1} )".format(t, task.period))

            print_list_abs.append("[{0} -> {1}, {2} -> {3}]".format(task.data[self.method_name]["a"], a,
                                                                    task.data[self.method_name]["b"],
                                                                    a_t * task.period))

            task.data[self.method_name]["a"] = a
            task.data[self.method_name]["b"] = a_t * task.period
        else:
            print_list_ceils.append(str(task.data[self.method_name]["a"]))
            print_list_abs.append(
                "[{0}, {1}]".format(task.data[self.method_name]["a"], task.data[self.method_name]["b"]))

        w = w + task.data[self.method_name]["a"]
        print_list_w.append(task.data[self.method_name]["a"])

    if printr:
        print("{0} suma techos: {1}".format("\t" * tabs, " + ".join(print_list_ceils)))
        print("{0} [a, b]:      {1}".format("\t" * tabs, " ; ".join(print_list_abs)))
        print("{0} w = {1} = {2}".format("\t" * tabs, " + ".join(str(e) for e in print_list_w), w))
        print("{0} slack = {1} - {2} - {3} + {4} = {5}".format("\t" * tabs, t, tc, w, wc, t - tc - w + wc))
        print("")

    return t - tc - w + wc, cc
