from slack.SlackExceptions import NegativeSlackException, DifferentSlackException
from slack import SlackFixed, SlackFixed15, SlackDavis, SlackFixed2, SlackFixed3, SlackHet, SlackFast, SlackFast2


def get_slack_methods():
    slack_methods = {"Fixed2": SlackFixed2.get_slack,
                     "Fixed3": SlackFixed3.get_slack,
                     "Fixed15": SlackFixed15.get_slack,
                     "Fixed": SlackFixed.get_slack,
                     "SlackHet": SlackHet.get_slack,
                     "Fast": SlackFast.get_slack,
                     "Fast2": SlackFast2.get_slack,
                     "Davis": SlackDavis.get_slack}
    return slack_methods


def reduce_slacks(tasks, amount, t):
    from math import fabs
    for task in tasks:
        task.data["ss"]["slack"] -= amount
        # DIRTY HACK
        if (fabs(task.data["ss"]["slack"]) < 0.00005):
            task.data["ss"]["slack"] = 0
        if task.data["ss"]["slack"] < 0:
            raise NegativeSlackException(t, task, "Scheduler")


def get_minimum_slack(tasks):
    # Find the system minimum slack and the time at which it occurs
    from sys import maxsize
    from math import fabs, isclose

    _min_slack = maxsize
    _min_slack_t = 0
    _min_slack_task = None

    for task in tasks:
        slack, ttma = task.data["ss"]["slack"], task.data["ss"]["ttma"]
        if isclose(slack, _min_slack) or (slack < _min_slack):
            if isclose(slack, _min_slack):
                if _min_slack_t <= ttma:
                    _min_slack_t = ttma
                    _min_slack_task = task
            else:
                _min_slack = slack
                _min_slack_t = ttma
                _min_slack_task = task

    return (_min_slack, _min_slack_t, _min_slack_task)


def multiple_slack_calc(tc, task, tasks, slack_methods: list) -> dict:
    # calculate slack with each method in slack_methods
    slack_results = [(m, get_slack_methods()[m](task, tasks, tc)) for m in slack_methods]

    # check for negative slacks
    for method, result in slack_results:
        if result["slack"] < 0:
            raise NegativeSlackException(tc, method, task.job.name if task.job else task.name)

    # verify that all the methods produces the same results
    ss = slack_results[0][1]["slack"]
    ttma = slack_results[0][1]["ttma"]
    for method, result in slack_results:
        if result["slack"] != ss or (result["ttma"] > 0 and result["ttma"] != ttma):
            raise DifferentSlackException(tc, task.job.name if task.job else task.name, method, slack_results)

    # return slack and ttma
    return {"slack": ss, "ttma": ttma, "ss_results": slack_results}
