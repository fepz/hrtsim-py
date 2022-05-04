"""
Rate Monotic algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler


class RM_mono(Scheduler):

    def init(self):
        self.ready_list = []

    def on_activate(self, job):
        self.ready_list.append(job)
        job.cpu.resched()

    def on_terminated(self, job):
        self.ready_list.remove(job)
        job.cpu.resched()

    def schedule(self, cpu):
        if self.ready_list:
            # job with the highest priority
            job = min(self.ready_list, key=lambda x: x.period)
            print("{:03.2f}\t{:1.1f}\t{:2.0f}".format(self.sim.now() / self.sim.cycles_per_ms, cpu.speed, 0))
        else:
            job = None


        return (job, cpu)
