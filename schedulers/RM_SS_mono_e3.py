"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing and energy consumption.
"""
import sys

from simso.core import Scheduler, Timer
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc, get_minimum_slack
from utils.rts import calculate_k, uf, rta
from schedtests import josephp
import copy


class RM_SS_mono_e3(Scheduler):

    def init(self):
        self.ready_list = []
        self.min_slack = 0
        self.min_slack_t = 0
        self.idle_start = 0
        self._energy = 0
        self._cpu = self.data["params"]["cpu"]
        self._cpu.set_lvl(1.0)
        self._rts = []
        self._lvlz = None

        # Find the minimum v/f level in which the RTS is schedulable.
        for lvl in self._cpu.lvls:
            if rta(self.data["params"]["rts"]["ptasks"], lvl[5]):
                self._lvlz = lvl
                for task in self.task_list:
                    task.data["C"] = task.data["C"] * lvl[5]
                break

        # Required fields for slack stealing.
        for ptask in self.data["params"]["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0
            ptask["ss"] = {'slack': 0, 'ttma': ptask["D"], 'di': 0, 'start_exec_time': 0, 'last_psi': 0,
                           'last_slack': 0, 'ii': 0}
            ptask["dvs"] = {'a': ptask["C"], 'b': 0}
            for ss_method in self.data["params"]["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        for atask in self.data["params"]["rts"]["atasks"]:
            atask["start_exec_time"] = 0

        for task in self.task_list:
            task.data["ss"]["slack"], task.data["ss"]["ttma"] = self._calc_slack(0, task)

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)

        # Select the minimum CPU v/f
        self._cpu.set_lvl(self._lvlz[6])
        self.processors[0].set_speed(self._cpu.curlvl[6])

        # Update the non-blocking execution part of each task
        for ptask in self.data["params"]["rts"]["ptasks"]:
            ptask["dvs"]["b"] = ptask["C"] * (self._cpu.curlvl[5] - 1)

        self._icf = self.min_slack_t

    def on_activate(self, job):
        self.print('A', job)
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        # Current simulation time.
        tc = self.sim.now() / self.sim.cycles_per_ms
        # Verify deadline.
        if job.exceeded_deadline:
            raise MissedDeadlineException(tc, job)
        # Executed time in ms since last execution.
        job_runtime = (self.sim.now() - job.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
        # Decrement higher priority tasks' slack.
        reduce_slacks(self.task_list[:(job.task.identifier - 1)], job_runtime, tc)
        # Calculate this task new slack.
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = self._calc_slack(tc, job.task)
        # Find the system minimum slack and the time at which it occurs.
        self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)
        # Compute energy consumption.
        self._energy += job.computation_time * self._cpu.curlvl[3]
        # Log event.
        self.print('E', job)
        # Remove the job from the CPU and reschedule
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        # Current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms
        # Preempt
        preempt = True
        job = None

        if cpu.running:
            # Current job executed time in ms.
            job_runtime = (self.sim.now() - cpu.running.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
            # Decrement higher priority tasks' slack.
            reduce_slacks(self.task_list[:(cpu.running.task.identifier - 1)], job_runtime, tc)
            # Find the system minimum slack and the time at which it occurs
            self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)
            # If the job is still executing its B part, do not preempt.
            if cpu.running.computation_time <= cpu.running.task.data["dvs"]["b"]:
                preempt = False
        else:
            # compute idle time
            if self.idle_start > 0:
                # Compute the idle time.
                elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
                reduce_slacks(self.task_list, elapsed_idle_time, tc)
                self._energy += elapsed_idle_time * self._cpu.curlvl[3]
                # Find the system minimum slack and the time at which it occurs
                self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)
                # Restore the CPU v/f
                self.f_min = (((self.min_slack_t - tc - self.min_slack) / (self.min_slack_t - tc)) * self._lvlz[6])
                self._cpu.set_lvl(self.f_min)
                self.processors[0].set_speed(self._cpu.curlvl[6])
                # Specify start of the new ICF
                self._icf = self.min_slack_t
                # Reset the idle start time.
                self.idle_start = 0

        # New ICF?
        if self._icf < self.min_slack_t:
            # Update the cpu v/f level
            self.f_min = (((self.min_slack_t - tc - self.min_slack) / (self.min_slack_t - tc)) * self._lvlz[6])
            self._cpu.set_lvl(self.f_min)
            self.processors[0].set_speed(self._cpu.curlvl[6])
            self._icf = self.min_slack_t

        if self.ready_list:
            if preempt:
                # Select the ready job with the highest priority (lowest period).
                job = min(self.ready_list, key=lambda x: x.period)
                # Update the execution start time.
                job.task.data["ss"]["start_exec_time"] = self.sim.now()
                self.print('S', job)
            else:
                # Do not remove the currently running job on the CPU.
                job = cpu.running
                #self._launch_btimer(cpu.running.task.data["dvs"]["b"] - cpu.running.computation_time)
        else:
            # Record idle time start
            self.idle_start = self.sim.now()
            # Change to the lowest CPU v/f level
            self._cpu.set_lvl(0)
            self.processors[0].set_speed(self._cpu.curlvl[6])

        return job, cpu

    def print(self, event, job):
        print("{:03.2f}\t{}\t{}\t{:1.3f}\t{:1.3f}\t{}\t{:1.3f}".format(
            self.sim.now() / self.sim.cycles_per_ms, job.name, event,
            job.cpu.speed, self._cpu.curlvl[6], self._cpu.curlvl[0], self._energy))

    def _calc_slack(self, tc, task):
        ss_result = multiple_slack_calc(tc, task, self.task_list, self.data["params"]["ss_methods"])
        return ss_result["slack"], ss_result["ttma"]

    def _launch_btimer(self, t):
        timer = Timer(self.sim, self._test(), None, 1000000, one_shot=True, in_ms=True)

    def _test(self):
        #self.processors[0].resched()
        print(self.sim.now())
