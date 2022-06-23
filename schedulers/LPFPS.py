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

    def init(self):
        self._ready_list = []
        self._early_activation = sys.maxsize
        self._energy = 0
        self.data["params"]["cpu"].set_lvl(1.0)

    def on_activate(self, job):
        job.cpu.set_speed(1.0)
        self.data["params"]["cpu"].set_lvl(job.cpu.speed)

        tmp_list = [math.floor((self.sim.now() / self.sim.cycles_per_ms) / task.period) 
                * task.period + task.period  for task in self.task_list]
        self._early_activation = min(tmp_list)

        self._ready_list.append(job)

        self.print('A', job)

        job.cpu.resched()

    def on_terminated(self, job):
        # Verify deadline
        if job.exceeded_deadline:
            raise MissedDeadlineException(tc, job)

        # Return the processor to its full speed (L1-L4 on Shin1999).
        job.cpu.set_speed(1.0)
        self.data["params"]["cpu"].set_lvl(job.cpu.speed)

        self._energy += (job.computation_time *
                self.data["params"]["cpu"].curlvl[3])

        self.print('E', job)

        # Remove the job from the CPU and reschedule
        self._ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        if self._ready_list:
            # Ready job with the highest priority (lowest period)
            job = min(self._ready_list, key=lambda x: x.period)

            if len(self._ready_list) == 1:
                # Compute new speed ratio
                ratio = (job.task.wcet - job.computation_time) / \
                    (self._early_activation - (self.sim.now() / self.sim.cycles_per_ms))

                if ratio <= 1.0:
                    cpu.set_speed(1.0 * ratio)
                    self.data["params"]["cpu"].set_lvl(cpu.speed)
            else:
                cpu.set_speed(1.0)
                self.data["params"]["cpu"].set_lvl(cpu.speed)

            self.print('S', job)

                    
        else:
            # Enter power down mode
            cpu.set_speed(0.0)
            self.data["params"]["cpu"].set_lvl(cpu.speed)

            job = None

        return job, cpu

    def print(self, event, job):
        print("{}\t{}\t{:03.2f}\t{:1.1f}\t{:1.1f}\t{:1.1f}".format(job.name, 
            event, self.sim.now() / self.sim.cycles_per_ms, job.cpu.speed, 
            self.data["params"]["cpu"].curlvl[6], self._energy))

