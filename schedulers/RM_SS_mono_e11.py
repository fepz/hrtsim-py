"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing and energy consumption.

v11: like v10, but do use an ideal processor

"""
import sys

from simso.core import Scheduler, Timer
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc, get_minimum_slack
from utils.rts import calculate_k, rta
from math import isclose


class RM_SS_mono_e11(Scheduler):

    def init(self):
        self.ready_list = []
        self.min_slack = 0
        self.min_slack_t = 0
        self.min_slack_s = 0
        self.idle_start = 0
        self._energy = 0
        self._cpu = self.data["cpu"]
        self._cpu.set_lvl(1.0)
        self._lvlz = None
        self._preempt = True
        self._finb = False
        self.f_min = 1.0
        self.f_zero = 1.0
        self._lvlb = None
        self._last_activation_time = -1
        self._icf_t = 0
        self._icf_calc_flag = False

        if not rta(self.data["rts"]["ptasks"]):
            print("No schedulable.")
            sys.exit(1)

        # Required fields for slack stealing.
        for ptask in self.data["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0
            ptask["ss"] = {'slack': 0, 'ttma': 0, 'di': 0}
            ptask["dvs"] = {'a': ptask["C"], 'b': 0, 'bp': 0, 'brun': False}
            for ss_method in self.data["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        # Calculate slack at t=0
        for task in self.task_list:
            task.data["ss"]["slack"], task.data["ss"]["ttma"] = self._calc_slack(0, task)

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, self.min_slack_t, self.min_slack_task = get_minimum_slack(self.task_list)

        self.f_zero = (self.min_slack_t - self.min_slack) / self.min_slack_t
        self.f_min = self.f_zero

        # Initial CPU v/f level
        self.processors[0].set_speed(self.f_zero)

        # Update the WCET of each task
        #for task in self.data["rts"]["ptasks"]:
        #    task["C"] = task["C"] * (1.0 / self.f_zero)

        self._icf_task = self.min_slack_task

        self._update_speed(0)

    def on_activate(self, job):
        self._print('A', job)
        self.ready_list.append(job)
        if self._last_activation_time < self.sim.now():
            self._last_activation_time = self.sim.now()
            if self._preempt:
                job.cpu.resched()

    def on_terminated(self, job):
        # Current simulation time.
        tc = self.sim.now() / self.sim.cycles_per_ms
        # Verify deadline.
        if job.exceeded_deadline:
            #raise MissedDeadlineException(tc, job)
            print("{:03.2f}\t{}\tDEADLINE MISS".format(tc, job.name))
        # Executed time in ms since last execution.
        job_runtime = (self.sim.now() - job.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
        # Decrement higher priority tasks' slack.
        reduce_slacks(self.task_list[:(job.task.identifier - 1)], job_runtime, tc)
        # Calculate this task new slack.
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = self._calc_slack(tc, job.task)
        # Find the system minimum slack and the time at which it occurs.
        self.min_slack, self.min_slack_t, min_slack_task = get_minimum_slack(self.task_list)
        # Compute energy consumption.
        self._energy += job.computation_time * self._cpu.curlvl[3]
        if job.task == self._icf_task:
            self._icf_calc_flag = True
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
                # Check if the B part has ended
                if self._finb is True:
                    reduce_slacks(self.task_list, job_runtime, tc)
                    self._preempt = True
                    self._finb = False
                else:
                    # Decrement higher priority tasks' slack.
                    reduce_slacks(self.task_list[:(cpu.running.task.identifier - 1)], job_runtime, tc)
            else:
                # compute idle time
                if self.idle_start > 0:
                    # Compute the idle time.
                    elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
                    # Reduce tasks' slacks
                    reduce_slacks(self.task_list, elapsed_idle_time, tc)
                    # Record energy consumption
                    self._energy += elapsed_idle_time * self._cpu.curlvl[3]
                    #  Restore the CPU v/f
                    self._restore_speed()
                    # Reset the idle start time.
                    self.idle_start = 0
                    # New IFC
                    self._icf_calc_flag = True

            # Find the system minimum slack and the time at which it occurs
            self.min_slack, self.min_slack_t, self.min_slack_task = get_minimum_slack(self.task_list)

            # Select the ready job with the highest priority (lowest period).
            job = min(self.ready_list, key=lambda x: x.period)
            # Update the execution start time.
            job.task.data["ss"]["start_exec_time"] = self.sim.now()

            # New ICF?
            if self._icf_calc_flag: # or isclose(tc, self._icf_t, rel_tol=0.0005):
                prev_icf_t = self._icf_t
                self._update_speed(tc)
                print("new icf {} - {} - {}".format(tc, self._icf_t, self.min_slack_task.name))
                self._icf_calc_flag = False
                self._icf_task = self.min_slack_task

            # Launch the scheduler when the task finish its B part.
            if job != cpu.running and job.computation_time == 0:
                if job.task.data["dvs"]["b"] > 0:
                    self._preempt = False
                    self._change_speed(job)
                    t = Timer(self.sim, self._timer, [], job.task.data["dvs"]["b"], cpu=self.processors[0])
                    t.start()

        else:
            # Record idle time start
            self.idle_start = self.sim.now()
            # Change to the lowest CPU v/f level
            self._lvlb = self._cpu.curlvl
            # Minimum cpu speed
            self._change_speed(None)

        if job:
            self._print('S', job)

        return job, cpu

    def _print(self, event, job):
        print("{:03.5f}\t{}\t{}\t{:1.5f}\t{:1.3f}\t{}".format(
            self.sim.now() / self.sim.cycles_per_ms, job.name, event, self.f_min, self._energy,
            '\t'.join(["{:03.2f}".format(task.data["ss"]["slack"]) for task in self.task_list])))

    def _calc_slack(self, tc, task):
        ss_result = multiple_slack_calc(tc, task, self.task_list, self.data["ss_methods"])
        return ss_result["slack"], ss_result["ttma"]

    def _update_speed(self, t):
        """
        Update the V/F level of the CPU.
        :return: None
        """
        self.f_min = ((self.min_slack_t - t - self.min_slack) / (self.min_slack_t - t))

        self._icf_t = self.min_slack_t

        # Update the non-blocking execution part of each task
        #for ptask in self.data["rts"]["ptasks"]:
        #    ptask["dvs"]["b"] = ptask["C"] * ((1.0 / self.f_min) - 1)
        for ptask in self.data["rts"]["ptasks"]:
           ptask["dvs"]["b"] = 0

        for ptask in self.task_list[:self.min_slack_task.identifier]:
           ptask.data["dvs"]["b"] = ptask.data["C"] * ((1.0 / self.f_min) - 1)

    def _change_speed(self, job):
        self.processors[0].set_speed(self.f_min if job is not None else 0)

    def _restore_speed(self):
        self.processors[0].set_speed(self.f_min)

    def _timer(self):
        self._finb = True
        self.processors[0].resched()
