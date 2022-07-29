"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing and energy consumption.
"""
import sys

from simso.core import Scheduler, Timer
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc, get_minimum_slack
from utils.rts import calculate_k, rta


class RM_SS_mono_e4(Scheduler):

    def init(self):
        self.ready_list = []
        self.min_slack = 0
        self.min_slack_t = 0
        self.idle_start = 0
        self._energy = 0
        self._cpu = self.data["cpu"]
        self._cpu.set_lvl(1.0)
        self._lvlz = None
        self._update_icf = False
        self._preempt = True
        self._finb = False

        # Found the minimum V/F level in which the periodic tasks are schedulable.
        for lvl in self._cpu.lvls:
            if rta(self.data["rts"]["ptasks"], lvl[5]):
                self._lvlz = lvl
                break

        if self._lvlz is None:
            print("No schedulable.")
            sys.exit(1)

        # Update the WCET of each task
        for task in self.data["rts"]["ptasks"]:
            task["C"] = task["C"] * self._lvlz[5]

        calculate_k(self.data["rts"]["ptasks"], self._lvlz[5])

        # Required fields for slack stealing.
        for ptask in self.data["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0
            ptask["ss"] = {'slack': 0, 'ttma': 0, 'di': 0}
            ptask["dvs"] = {'a': ptask["C"], 'b': 0, 'brun': False}
            for ss_method in self.data["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        for atask in self.data["rts"]["atasks"]:
            atask["start_exec_time"] = 0

        # Calculate slack at t=0
        for task in self.task_list:
            task.data["ss"]["slack"], task.data["ss"]["ttma"] = self._calc_slack(0, task)

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, self.min_slack_t, self.min_slack_task = get_minimum_slack(self.task_list)

        # Select the minimum CPU v/f
        self._update_speed()

        # Update the non-blocking execution part of each task
        for ptask in self.data["rts"]["ptasks"]:
            ptask["dvs"]["b"] = ptask["C"] * (self._cpu.curlvl[5] - 1)

    def on_activate(self, job):
        self._print('A', job)
        self.ready_list.append(job)
        if self._preempt:
            job.cpu.resched()

    def on_terminated(self, job):
        # Current simulation time.
        tc = self.sim.now() / self.sim.cycles_per_ms
        # Verify deadline.
        if job.exceeded_deadline:
            #raise MissedDeadlineException(tc, job)
            print("{:03.2f}\t{}\tDEADLINE MISS".format(tc, job.name))
        if job.task == self.min_slack_task:
            self._update_icf = True
        # Executed time in ms since last execution.
        job_runtime = (self.sim.now() - job.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
        # Decrement higher priority tasks' slack.
        reduce_slacks(self.task_list[:(job.task.identifier - 1)], job_runtime, tc)
        # Calculate this task new slack.
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = self._calc_slack(tc, job.task)
        # Find the system minimum slack and the time at which it occurs.
        self.min_slack, self.min_slack_t, min_slack_task = get_minimum_slack(self.task_list)
        if self._update_icf is True:
            self.min_slack_task = min_slack_task
        # Compute energy consumption.
        self._energy += job.computation_time * self._cpu.curlvl[3]
        # Log event.
        self._print('E', job)
        # Remove the job from the CPU and reschedule
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        # Current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms
        job = None

        if cpu.running:
            # Current job executed time in ms.
            job_runtime = (self.sim.now() - cpu.running.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
            # Check if the B part has ended
            if self._finb is True:
                reduce_slacks(self.task_list, job_runtime, tc)
                self._preempt = True
                self._finb = False
            else:
                # Decrement higher priority tasks' slack.
                reduce_slacks(self.task_list[:(cpu.running.task.identifier - 1)], job_runtime, tc)
            # Find the system minimum slack and the time at which it occurs
            self.min_slack, self.min_slack_t, _ = get_minimum_slack(self.task_list)
        else:
            # compute idle time
            if self.idle_start > 0:
                # Compute the idle time.
                elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
                # Reduce tasks' slacks
                reduce_slacks(self.task_list, elapsed_idle_time, tc)
                # Record energy consumption
                self._energy += elapsed_idle_time * self._cpu.curlvl[3]
                # Find the system minimum slack and the time at which it occurs
                self.min_slack, self.min_slack_t, _ = get_minimum_slack(self.task_list)
                #  Restore the CPU v/f
                self._restore_speed()
                # Reset the idle start time.
                self.idle_start = 0

        # New ICF?
        if self._update_icf is True:
            self._update_icf = False
            self._update_speed()

        if len(self.ready_list) > 0:
            if self._preempt:
                # Select the ready job with the highest priority (lowest period).
                job = min(self.ready_list, key=lambda x: x.period)
                # Update the execution start time.
                job.task.data["ss"]["start_exec_time"] = self.sim.now()
                self._print('S', job)

                if job != cpu.running:
                    if job.computation_time == 0 and job.task.data["dvs"]["b"] > 0:
                        self._preempt = False
                        self._finb = False
                        t = Timer(self.sim, self._timer, [], job.task.data["dvs"]["b"], cpu=self.processors[0])
                        t.start()
            else:
                # Do not remove the currently running job on the CPU.
                job = cpu.running
        else:
            # Record idle time start
            self.idle_start = self.sim.now()
            # Change to the lowest CPU v/f level
            self._cpu.set_lvl(0)
            self.processors[0].set_speed(self._cpu.curlvl[6])

        return job, cpu

    def _print(self, event, job):
        print("{:03.2f}\t{}\t{}\t{:1.3f}\t{:1.3f}\t{:1.3f}\t{}\t{:1.3f}".format(
            self.sim.now() / self.sim.cycles_per_ms, job.name, event,
            self.f_min, job.cpu.speed, self._cpu.curlvl[6], self._cpu.curlvl[0], self._energy))

    def _calc_slack(self, tc, task):
        ss_result = multiple_slack_calc(tc, task, self.task_list, self.data["ss_methods"])
        return ss_result["slack"], ss_result["ttma"]

    def _update_speed(self):
        """
        Update the V/F level of the CPU.
        :return: None
        """
        tc = self.sim.now() / self.sim.cycles_per_ms
        self.f_min = ((self.min_slack_t - tc - self.min_slack) / (self.min_slack_t - tc)) * self._lvlz[6]
        self._cpu.set_lvl(self.f_min)
        self.processors[0].set_speed(self._cpu.curlvl[6])
        self._lvlb = self._cpu.curlvl

        # Update the non-blocking execution part of each task
        for ptask in self.data["rts"]["ptasks"]:
            ptask["dvs"]["b"] = ptask["C"] * (self._cpu.curlvl[5] - 1)

    def _restore_speed(self):
        self._cpu.set_lvl(self._lvlb[6])
        self.processors[0].set_speed(self._cpu.curlvl[6])

    def _timer(self):
        self._finb = True
        self.processors[0].resched()


