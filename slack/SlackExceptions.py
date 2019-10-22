class NegativeSlackException(Exception):
    def __init__(self, t, task, method):
        Exception.__init__(self, 'Negative slack for task {:s} at t={:d}: s={:d}, method {:s}'.format(task.name, t,
                                                                                                      task.data[
                                                                                                          "slack"],
                                                                                                      method))


class DifferentSlackException(Exception):
    def __init__(self, t, job, method):
        Exception.__init__(self, 'Slack result differ for job {:s} at t={:d} for method {:s}'.format(job.name, t, method))
