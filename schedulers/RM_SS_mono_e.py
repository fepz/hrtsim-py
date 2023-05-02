"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing and energy consumption.
"""
import sys

from simso.core import Scheduler
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc, get_minimum_slack
from utils.rts import calculate_k
from schedtests import josephp
import copy


class RM_SS_mono_e(Scheduler):

    def init(self):
        self.ready_list = []
        self.min_slack = 0
        self.min_slack_t = 0
        self.idle_start = 0
        self._energy = 0
        self._cpu = self.data["params"]["cpu"]
        self._cpu.set_lvl(1.0)
        self._rts = []

        f = self._cpu.get_lvl(-1)
        for lvl in self._cpu.lvls:
            rts_in_lvl = copy.deepcopy(self.data["params"]["rts"])

            for ptask in rts_in_lvl["ptasks"]:
                ptask["C"] = (f[0] / lvl[0]) * ptask["C"]

            josephp(rts_in_lvl["ptasks"])

            # The K values are also used as the slack at t=0
            calculate_k(rts_in_lvl["ptasks"])

            for ptask in rts_in_lvl["ptasks"]:
                ptask["start_exec_time"] = 0

                ptask["ss"] = {'slack': ptask["k"], 'ttma': ptask["D"], 'di': 0, 'start_exec_time': 0, 'last_psi': 0,
                               'last_slack': 0, 'ii': 0}

                for ss_method in self.data["params"]["ss_methods"]:
                    ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

            self._rts.append(rts_in_lvl)

        calculate_k(self.data["params"]["rts"]["ptasks"])

        # Required fields for slack stealing simulation.
        for ptask in self.data["params"]["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0

            ptask["ss"] = {'slack': ptask["k"], 'ttma': ptask["D"], 'di': 0, 'start_exec_time': 0, 'last_psi': 0,
                           'last_slack': 0, 'ii': 0}

            for ss_method in self.data["params"]["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        for atask in self.data["params"]["rts"]["atasks"]:
            atask["start_exec_time"] = 0

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)

        self.f_min = ((self.min_slack_t - self.min_slack) / self.min_slack_t)
        self._cpu.set_lvl(self.f_min)
        self.processors[0].set_speed(self._cpu.curlvl[6])

    def on_activate(self, job):
        self.print('A', job)
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
        ss_result = multiple_slack_calc(tc, job, self.task_list, self.data["params"]["ss_methods"])

        # log results
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = ss_result["slack"], ss_result["ttma"]

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)

        self._energy += job.computation_time * self._cpu.curlvl[3]

        self.print('E', job)

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
        else:
            # compute idle time
            if self.idle_start > 0:
                elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
                t = self.sim.now() / self.sim.cycles_per_ms
                reduce_slacks(self.task_list, elapsed_idle_time, t)
                self._energy += elapsed_idle_time * self._cpu.curlvl[3]
                self.idle_start = 0

                # Find the system minimum slack and the time at which it occurs
                self.min_slack, self.min_slack_t = get_minimum_slack(self.task_list)

                tc = self.sim.now() / self.sim.cycles_per_ms
                self.f_min = ((self.min_slack_t - tc - self.min_slack) / (self.min_slack_t - tc))
                self._cpu.set_lvl(self.f_min)
                self.processors[0].set_speed(self._cpu.curlvl[6])

        if self.ready_list:
            # ready job with the highest priority (lowest period)
            job = min(self.ready_list, key=lambda x: x.period)

            # update execution start time
            job.task.data["ss"]["start_exec_time"] = self.sim.now()

            self.print('S', job)
        else:
            # idle time start
            self.idle_start = self.sim.now()
            # set CPU to minimum level
            #self._cpu.set_lvl(0)
            #self.processors[0].set_speed(self._cpu.curlvl[6])

            job = None

        return job, cpu

    def print(self, event, job):
        print("{:03.2f}\t{}\t{}\t{:1.3f}\t{:1.3f}\t{}\t{:1.3f}".format(
            self.sim.now() / self.sim.cycles_per_ms, job.name, event,
            job.cpu.speed, self._cpu.curlvl[6], self._cpu.curlvl[0], self._energy))
