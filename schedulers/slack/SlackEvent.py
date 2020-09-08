

class SlackEvent:
    CALC_SLACK = 10

    count = 0

    def __init__(self, job, slack_results, event, cpu=None):
        self.event = event
        self.job = job
        self.cpu = cpu
        self.slack = job.task.data["ss"]["slack"]
        self.slack_results = slack_results
        SlackEvent.count += 1
        self.id_ = SlackEvent.count
