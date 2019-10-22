class MissedDeadlineException(Exception):
    def __init__(self, t, job):
        Exception.__init__(self, 'Missed deadline for job {:s} at t={:d}'.format(job.name, t))
