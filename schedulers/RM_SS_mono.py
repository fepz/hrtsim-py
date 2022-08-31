"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing.
"""
from simso.core import Scheduler
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc, get_minimum_slack
from utils.rts import calculate_k


class RM_SS_mono(Scheduler):

    def init(self):
        self.ready_list = []
        self.min_slack = 0
        self.idle_start = 0
        self._last_activation_time = -1

        calculate_k(self.data["rts"]["ptasks"])

        # Required fields for slack stealing simulation.
        for ptask in self.data["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0
            ptask["ss"] = {'slack': ptask["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0,
                           'last_slack': 0, 'ii': 0}
            for ss_method in self.data["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        for atask in self.data["rts"]["atasks"]:
            atask["start_exec_time"] = 0

        # Calculate slack at t=0
        for task in self.task_list:
            task.data["ss"]["slack"], task.data["ss"]["ttma"] = self._calc_slack(0, task)

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, _, _ = get_minimum_slack(self.task_list)

    def on_activate(self, job):
        self._print('A', job)
        self.ready_list.append(job)
        if self._last_activation_time < self.sim.now():
            self._last_activation_time = self.sim.now()
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

        # Calculate this task new slack.
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = self._calc_slack(tc, job.task)

        # Find the system minimum slack and the time at which it occurs.
        self.min_slack, _, _ = get_minimum_slack(self.task_list)

        # Log event.
        self._print('E', job)

        # Remove the job from the CPU and reschedule
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        # Current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms
        job = cpu.running

        if len(self.ready_list) > 0:
            if cpu.running:
                # Current job executed time in ms.
                job_runtime = (self.sim.now() - cpu.running.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
                # Decrement higher priority tasks' slack.
                reduce_slacks(self.task_list[:(cpu.running.task.identifier - 1)], job_runtime, tc)
            else:
                # compute idle time
                if self.idle_start > 0:
                    # Compute the idle time.
                    elapsed_idle_time = tc / self.sim.cycles_per_ms
                    # Reduce tasks' slacks
                    reduce_slacks(self.task_list, elapsed_idle_time, tc)
                    # Reset the idle start time.
                    self.idle_start = 0

            # Find the system minimum slack and the time at which it occurs
            self.min_slack, _, _ = get_minimum_slack(self.task_list)

            # Select the ready job with the highest priority (lowest period).
            job = min(self.ready_list, key=lambda x: x.period)
            # Update the execution start time.
            job.task.data["ss"]["start_exec_time"] = self.sim.now()
        else:
            # Record idle time start
            self.idle_start = self.sim.now()

        if job:
            self._print('S', job)

        return job, cpu

    def _print(self, event, job):
        print("{:03.2f}\t{}\t{}\t{}".format(
            self.sim.now() / self.sim.cycles_per_ms, job.name, event,
            '\t'.join(["{:03.2f}".format(task.data["ss"]["slack"]) for task in self.task_list])))

    def _calc_slack(self, tc, task):
        ss_result = multiple_slack_calc(tc, task, self.task_list, self.data["ss_methods"])
        return ss_result["slack"], ss_result["ttma"]
