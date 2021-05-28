class NegativeSlackException(Exception):
    def __init__(self, t, task, method):
        Exception.__init__(self, 'Negative slack! method {:s}, task {:s}, t={:f}, s={:d}'.format(method, task.name, t,
                                                                                                 task.data['slack']))


class DifferentSlackException(Exception):
    def __init__(self, t, job, method, results):
        err_str = "\n".join(["\t{0:} {1:} {2:} {3:}".format(m, r["slack"], r["ttma"], r["cc"]) for m, r in results])
        Exception.__init__(self, 'Slack result differ for job {:s} at t={:f} for method {:s}:\n{:s}'.format(job.name, t, method, err_str))
