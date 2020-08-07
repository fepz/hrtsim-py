class NegativeSlackException(Exception):
    def __init__(self, t, task, method):
        Exception.__init__(self, 'Negative slack! method {:s}, task {:s}, t={:f}, s={:d}'.format(method, task.name, t,
                                                                                                 task.data['slack']))


class DifferentSlackException(Exception):
    def __init__(self, t, job, method, results):
        Exception.__init__(self, 'Slack result differ for job {:s} at t={:f} for method {:s}:\n\t{}'.format(job.name, t, method, results))
