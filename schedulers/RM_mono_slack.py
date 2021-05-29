"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing.
"""
from simso.core import Scheduler
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc


class RM_mono_slack(Scheduler):

    def __init__(self, sim, scheduler_info, **kwargs):
        super().__init__(sim, scheduler_info, **kwargs)
        self.ready_list = []
        self.min_slack = 0
        self.idle_start = 0
        self._sim = sim

    def on_activate(self, job):
        # compute idle time
        if job.cpu.running is None and self.idle_start > 0:
            elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
            t = self.sim.now() / self.sim.cycles_per_ms
            reduce_slacks(self.task_list, elapsed_idle_time, t)
            self.idle_start = 0

        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        # current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms

        # verify deadline
        if job.exceeded_deadline:
            raise MissedDeadlineException(tc, job)

        # executed time in ms since last execution
        job_runtime = (self.sim.now() - job.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms

        # decrement higher priority tasks slack
        reduce_slacks(self.task_list[:(job.task.identifier - 1)], job_runtime, tc)

        # calculate task slack
        ss_result = multiple_slack_calc(tc, job, self.task_list, self.data["slack_methods"])

        # print the slack results to stdout
        for k, v in ss_result["ss_results"]:
            print("{0:} {1:} {2:} {3:} {4:} {5:} {6:} {7:}".format(job.name.split("_")[1], job.name.split("_")[2],
                                                              tc, v["slack"], v["ttma"], v["cc"], v["interval_length"], k))

        # log results
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = ss_result["slack"], ss_result["ttma"]

        # Find system new minimum slack
        self.min_slack = min([task.data["ss"]["slack"] for task in self.task_list])

        # Remove the job from the CPU and reschedule
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        if cpu.running:
            # current simulation time
            tc = self.sim.now() / self.sim.cycles_per_ms

            # current job executed time in ms
            job_runtime = (self.sim.now() - cpu.running.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms

            # decrement higher priority tasks slack
            reduce_slacks(self.task_list[:(cpu.running.task.identifier - 1)], job_runtime, tc)

            # find system new minimum slack
            self.min_slack = min([task.data["ss"]["slack"] for task in self.task_list])

        if self.ready_list:
            # ready job with the highest priority (lowest period)
            job = min(self.ready_list, key=lambda x: x.period)

            # update execution start time
            job.task.data["ss"]["start_exec_time"] = self.sim.now()
        else:
            # idle time start
            self.idle_start = self.sim.now()

            job = None

        return job, cpu
