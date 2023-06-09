"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing and energy consumption.

v21: starting from zero ...

"""
import sys

from simso.core import Scheduler, Timer
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc, get_minimum_slack
from utils.rts import calculate_k, rta
from math import isclose


class RM_SS_mono_e21(Scheduler):

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
        self._lvlb = None
        self._last_activation_time = -1
        self._icf_t = 0
        self._cpu_level_current = None
        self._cpu_level_min = None

        # Found the minimum V/F level in which the periodic tasks are schedulable.
        for lvl in self._cpu.lvls:
            if rta(self.data["rts"]["ptasks"], lvl[5]):
                self._lvlz = lvl
                break
        else:
            print("No schedulable.")
            sys.exit(1)

        # Initial CPU v/f level
        self.f_min = self._lvlz[6]
        self._cpu.set_lvl(self._lvlz[6])
        self.processors[0].set_speed(self._cpu.curlvl[6])

        self._cpu_level_current = self._lvlz

        # Update the WCET of each task
        for task in self.data["rts"]["ptasks"]:
            task["C"] = task["C"] * self._lvlz[5]

        calculate_k(self.data["rts"]["ptasks"])

        # Required fields for slack stealing.
        for ptask in self.data["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0
            ptask["ss"] = {'slack': 0, 'ttma': 0, 'di': 0}
            ptask["dvs"] = {'a': ptask["C"], 'b': 0, 'bp': 0, 'brun': False, 'wb': 'b', 'leveldvs': None, 'runtime': 0}
            for ss_method in self.data["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        if "atasks" in self.data["rts"].keys():
            for atask in self.data["rts"]["atasks"]:
                atask["start_exec_time"] = 0

        # Calculate slack at t=0
        for task in self.task_list:
            task.data["ss"]["slack"], task.data["ss"]["ttma"] = self._calc_slack(0, task)

        # Find the system minimum slack and the time at which it occurs
        self.min_slack, self.min_slack_t, self.min_slack_task = get_minimum_slack(self.task_list)
        self._icf_task = None
        self._icf_t = 0


    def on_activate(self, job):
        #self._print('A', job)
        self.ready_list.append(job)

        job.task.data["dvs"]["b"] = job.task.data["C"]
        job.task.data["dvs"]["runtime"] = job.task.data["C"]
        job.task.data["dvs"]["c_at_p-1"] = 0
        job.task.data["dvs"]["c_at_p"] = 0
        job.task.data["dvs"]["leveldvs"] = self._lvlz
        if self._last_activation_time < self.sim.now():
            self._last_activation_time = self.sim.now()
            if self._preempt:
                job.cpu.resched()


    def on_terminated(self, job):
        # Current simulation time.
        tc = self.sim.now() / self.sim.cycles_per_ms
        # Verify deadline.
        if job.exceeded_deadline:
            print("{:03.2f}\t{}\tDEADLINE MISS".format(tc, job.name))
            raise MissedDeadlineException(tc, job)
        # Executed time in ms since last execution.
        job_runtime = (self.sim.now() - job.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
        # Decrement higher priority tasks' slack.
        reduce_slacks(self.task_list[:(job.task.identifier - 1)], job_runtime, tc)
        if job_runtime > job.task.data["C"]:
            reduce_slacks(self.task_list[(job.task.identifier):], job_runtime - job.task.data["C"], tc)
        # Calculate this task new slack.
        job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = self._calc_slack(tc, job.task)
        # Find the system minimum slack and the time at which it occurs.
        self.min_slack, self.min_slack_t, self.min_slack_task = get_minimum_slack(self.task_list)
        # Compute energy consumption.
        self._energy += job.computation_time * self._cpu.curlvl[3]
        # Log event.
        #self._print('E', job)
        # Remove the job from the CPU and reschedule
        self.ready_list.remove(job)

        job.cpu.resched()


    def schedule(self, cpu):
        t = self.sim.now() / self.sim.cycles_per_ms

        nextstop = self._nextstop(t)

        error = 0.1e-9

        if len(self.ready_list) == 0:
            # Record idle time start
            self.idle_start = self.sim.now()
            return None, cpu

        # Select the ready job with the highest priority (lowest period).
        job = min(self.ready_list, key=lambda x: x.period)
        # Update the execution start time.
        job.task.data["ss"]["start_exec_time"] = self.sim.now()

        if job != cpu.running and cpu.running is not None:
            if cpu.running.task.data["dvs"]["b"] > cpu.running.task.data["C"]:
                reduce_slacks(self.task_list, cpu.running.task.data["dvs"]["b"] - cpu.running.task.data["C"], t)

        runtime = job.task.data["dvs"]["b"] - job.computation_time
        runtime2 = runtime / job.task.data["C"]

        if runtime2 == 1:
            if (nextstop - t + job.task.data["C"] > error) and (len(self.ready_list) == 1):
                pass
            else:
                if self._icf_task != self.min_slack_task or self._icf_t != self.min_slack_t:
                    self.f_ideal = ((self.min_slack_t - t - self.min_slack) / (self.min_slack_t - t)) * self._lvlz[6]
                    self._icf_task = self.min_slack_task
                    self._icf_t = self.min_slack_t
                    # level p-1 and p
                    lvl_tup = self._cpu.get_adjacent_lvls(self.f_ideal)
                    if lvl_tup[0][0] < lvl_tup[1][0]:
                        lvl_tup = (lvl_tup[0], lvl_tup[0])
                    self._cpu_level_p1 = lvl_tup[0]
                    self._cpu_level_p = lvl_tup[1]
                    self._slacksob = (self.min_slack_t - t) * (1 - (self.f_ideal / self._cpu_level_p1[6]))
                    self._slackb = job.task.data["C"] * self.min_slack / (self.min_slack_t - t - self.min_slack)

                job.task.data["dvs"]["b"] = job.task.data["C"] * (self._lvlz[0] / self._cpu_level_p[0])

                if (job.task.data["dvs"]["b"] - job.task.data["C"] - self._slacksob - self._slackb > error) \
                        or (job.task.data["dvs"]["b"] - job.task.data["C"] - self.min_slack > error):
                    job.task.data["dvs"]["b"] = job.task.data["C"] * (self._lvlz[0] / self._cpu_level_p1[0])
                    job.task.data["dvs"]["leveldvs"] = self._cpu_level_p1
                else:
                    amount = (job.task.data["dvs"]["b"] - job.task.data["C"] * (self._lvlz[0] / self._cpu_level_p1[0]))
                    self._slacksob -= amount
                    job.task.data["dvs"]["leveldvs"] = self._cpu_level_p
        else:
            if nextstop - t + runtime > error and len(self.ready_list) == 1 and (job.absolute_deadline - nextstop) < error:
                pass
            else:
                self.f_ideal = ((self.min_slack_t - t - self.min_slack) / (self.min_slack_t - t)) * self._lvlz[6]
                self._icf_task = self.min_slack_task
                self._icf_t = self.min_slack_t
                # level p-1 and p
                lvl_tup = self._cpu.get_adjacent_lvls(self.f_min)
                if lvl_tup[0][0] < lvl_tup[1][0]:
                    lvl_tup = (lvl_tup[0], lvl_tup[0])
                self._cpu_level_p1 = lvl_tup[0]
                self._cpu_level_p = lvl_tup[1]
                self._slacksob = (self.min_slack_t - t) * (1 - (self.f_ideal / self._cpu_level_p1[6]))
                self._slackb = runtime * self.min_slack / (self.min_slack_t - t - self.min_slack)

                job.task.data["dvs"]["b"] = runtime * (job.task.data["dvs"]["leveldvs"][0] / self._cpu_level_p[0])

                if (job.task.data["dvs"]["b"] - runtime - self._slacksob - self._slackb > error) \
                        or (job.task.data["dvs"]["b"] - runtime - self.min_slack > error):
                    job.task.data["dvs"]["b"] = runtime * (job.task.data["dvs"]["leveldvs"][0] / self._cpu_level_p1[0])
                    job.task.data["dvs"]["leveldvs"] = self._cpu_level_p1
                else:
                    self._slacksob -= (job.task.data["dvs"]["b"] - runtime * (job.task.data["dvs"]["leveldvs"][0] / self._cpu_level_p1[0]))
                    job.task.data["dvs"]["leveldvs"] = self._cpu_level_p

        if job:
            self._print('S', job)
            self.processors[0].set_speed(job.task.data["dvs"]["leveldvs"][6])

        return job, cpu

    def schedule2(self, cpu):
        # Current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms
        job = cpu.running

        if len(self.ready_list) > 0:
            if cpu.running:
                # Current job executed time in ms.
                job_runtime = (self.sim.now() - cpu.running.task.data["ss"]["start_exec_time"]) / self.sim.cycles_per_ms
                job.task.data["dvs"]["r"] += job_runtime
                # Check if the B part has ended
                if self._finb is True:
                    if job.task.data["dvs"]["wb"] == "bp":
                        self.min_slack_s -= (job.task.data["dvs"]["bp"] - job.task.data["dvs"]["b"])
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
                    # Find the system minimum slack and the time at which it occurs
                    self.min_slack, self.min_slack_t, self.min_slack_task = get_minimum_slack(self.task_list)
                    # Record energy consumption
                    self._energy += elapsed_idle_time * self._cpu.curlvl[3]
                    #  Restore the CPU v/f
                    self._restore_speed()
                    # Reset the idle start time.
                    self.idle_start = 0

            # Select the ready job with the highest priority (lowest period).
            job = min(self.ready_list, key=lambda x: x.period)
            # Update the execution start time.
            job.task.data["ss"]["start_exec_time"] = self.sim.now()

            # New ICF?
            if self._icf_task != self.min_slack_task or self._icf_t != self.min_slack_t:
                self._update_speed(tc)
                print("new icf {} - {} - {} - {}".format(tc, self._icf_t, self.min_slack_task.name, self.min_slack_s))
                self._icf_task = self.min_slack_task
                self._icf_t = self.min_slack_t

            # Launch the scheduler when the task finish its B part.
            if job != cpu.running:
                self._change_speed(job, tc)
                if job.computation_time == 0:
                    wb = job.task.data["dvs"]["wb"]
                    if job.task.data["dvs"][wb] > 0:
                        self._preempt = False
                        t = Timer(self.sim, self._timer, [], job.task.data["dvs"][wb], cpu=self.processors[0])
                        t.start()

            self.processors[0].set_speed(job.task.data["dvs"]["freq"][6])

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
        print("{:03.9f}\t{}\t{}\t{:1.3f}\t{:4.3f}\t{:4.3f}\t{:4.3f}\t{}".format(
            self.sim.now() / self.sim.cycles_per_ms, job.name, event,
            self.f_min, job.cpu.speed, self.min_slack_s, min([task.data["ss"]["slack"] for task in self.task_list]),
            '\t'.join(["{:03.3f}".format(task.data["ss"]["slack"]) for task in self.task_list])))

    def _calc_slack(self, tc, task):
        ss_result = multiple_slack_calc(tc, task, self.task_list, self.data["ss_methods"])
        return ss_result["slack"], ss_result["ttma"]

    def _update_speed(self, t):
        """
        Update the V/F level of the CPU.
        :return: None
        """
        self.f_min = ((self.min_slack_t - t - self.min_slack) / (self.min_slack_t - t)) * self._lvlz[6]

        # level p-1 and p
        self.lvl_tup = self._cpu.get_adjacent_lvls(self.f_min)
        if self.lvl_tup[0][0] < self.lvl_tup[1][0]:
            self.lvl_tup = (self.lvl_tup[0], self.lvl_tup[0])

        # slack sobrante
        self.min_slack_s = (self.min_slack_t - t) * (1 - (self.f_min / self.lvl_tup[0][6]))

        self._icf_t = self.min_slack_t

        # Update the non-blocking execution part of each task
        for ptask in self.data["rts"]["ptasks"]:
            ptask["dvs"]["b"] = ptask["C"] * ((self._lvlz[0] / self.lvl_tup[0][0]) - 1)
            ptask["dvs"]["bp"] = ptask["C"] * ((self._lvlz[0] / self.lvl_tup[1][0]) - 1)
            ptask["dvs"]["r_b"] =ptask["C"] * (self._lvlz[0] / self.lvl_tup[0][0])
            ptask["dvs"]["r_bp"] =ptask["C"] * (self._lvlz[0] / self.lvl_tup[1][0])

    def _change_speed(self, job, tc=0):
        if job:
            if job.task.data["dvs"]["r"] > 0:
                task_runtime = job.task.data["dvs"]["r"]
            else:
                task_runtime = job.task.data["C"]
            if job.task.data["dvs"]["r"] > 0:
                slack_b = ((job.task.data["dvs"]["r_bp"]) - job.task.data["dvs"]["r"]) * self.min_slack / (self.min_slack_t - tc - self.min_slack)
            else:
                slack_b = job.task.data["C"] * self.min_slack / (self.min_slack_t - tc - self.min_slack)
            if job.task.data["dvs"]["bp"] <= self.min_slack_s + slack_b:
                self._cpu.set_lvl(self.lvl_tup[1][6])
                job.task.data["dvs"]["wb"] = "bp"
            else:
                self._cpu.set_lvl(self.lvl_tup[0][6])
                job.task.data["dvs"]["wb"] = "b"
            self.processors[0].set_speed(self._cpu.curlvl[6])
            job.task.data["dvs"]["freq"] = self._cpu.curlvl
        else:
            self._cpu.set_lvl(0)
            self.processors[0].set_speed(self._cpu.curlvl[6])


    def _change_speed_bkp(self, job, tc=0):
        from math import isclose
        if job:
            dif = job.task.data["dvs"]["bp"] - job.task.data["dvs"]["b"]
            slackb = job.task.data["C"] * self.min_slack / (self.min_slack_t - tc - self.min_slack)
            s = self.min_slack_s + slackb
            if s > dif or isclose(s, dif, rel_tol=1e-05):
                self._cpu.set_lvl(self.lvl_tup[1][6])
                job.task.data["dvs"]["wb"] = "bp"
            else:
                self._cpu.set_lvl(self.lvl_tup[0][6])
                job.task.data["dvs"]["wb"] = "b"
            self.processors[0].set_speed(self._cpu.curlvl[6])
            job.task.data["dvs"]["freq"] = self._cpu.curlvl
        else:
            self._cpu.set_lvl(0)
            self.processors[0].set_speed(self._cpu.curlvl[6])

    def _restore_speed(self):
        self._cpu.set_lvl(self._lvlb[6])
        self.processors[0].set_speed(self._cpu.curlvl[6])

    def _timer(self):
        self._finb = True
        self.processors[0].resched()

    def _nextstop(self, t):
        import math
        tmp_list = [math.floor(t / task.period) * task.period + task.period for task in self.task_list]
        return min(tmp_list)

