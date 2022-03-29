"""
Low Power Fixed Priority Scheduling -- Shin 1999

From the work "Power conscious Fixed Priority Scheduling for Hard Real-Time
Systems" by Youngsoo Shin and Kiyoung Choi.
"""
from simso.core import Scheduler
from schedulers.MissedDeadlineException import MissedDeadlineException
import sys
import math


class LPFPS(Scheduler):

    def __init__(self, sim, scheduler_info, **kwargs):
        super().__init__(sim, scheduler_info, **kwargs)
        self.ready_list = []
        self.idle_start = 0
        self._sim = sim
        self._early_activation = sys.maxsize

    def on_activate(self, job):
        # compute idle time
        if job.cpu.running is None and self.idle_start > 0:
            elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
            t = self.sim.now() / self.sim.cycles_per_ms
            self.idle_start = 0

        tmp_list = [math.floor(((self.sim.now() / self.sim.cycles_per_ms) / task.period) * task.period) + task.period  for task in self.task_list]
        self._early_activation = min(tmp_list)

        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        # verify deadline
        #if job.exceeded_deadline:
        #    raise MissedDeadlineException(tc, job)

        # return the processor to its full speed (L1-L4 on Shin1999).
        job.cpu.set_speed(1.0)

        # Remove the job from the CPU and reschedule
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # ready job with the highest priority (lowest period)
            job = min(self.ready_list, key=lambda x: x.period)

            if len(self.ready_list) == 1:
                # compute new speed ratio
                ratio = (job.task.wcet - job.computation_time) / ( self._early_activation - ( self.sim.now() / self.sim.cycles_per_ms ) )

                if ((1.0 * ratio) <= 1.0):
                    cpu.set_speed(1.0 * ratio)
        else:
            # idle time start
            self.idle_start = self.sim.now()

            # enter power down mode
            cpu.set_speed(0.0)

            job = None

        return job, cpu
