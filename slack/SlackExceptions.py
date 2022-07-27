class NegativeSlackException(Exception):
    def __init__(self, t, task, method):
        if "slack" in task.data:
            Exception.__init__(self, 'Negative slack! method {:s}, task {:s}, t={:f}, s={:f}'.format(method, task.name, t, task.data['ss']['slack']))
        else:
            Exception.__init__(self, 'Negative slack! method {:s}, task {:s}, t={:f}'.format(method, task.name, t))


class DifferentSlackException(Exception):
    def __init__(self, t, name, method, results):
        err_str = "\n".join(["\t{0:} {1:} {2:} {3:}".format(m, r["slack"], r["ttma"], r["cc"]) for m, r in results])
        Exception.__init__(self, 'Slack result differ for job {:s} at t={:f} for method {:s}:\n{:s}'.format(name, t, method, err_str))
