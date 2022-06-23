"""
Rate Monotic algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler


class RM_mono(Scheduler):

    def init(self):
        self._ready_list = []
        self._energy = 0
        self.data["params"]["cpu"].set_lvl(1.0)

    def on_activate(self, job):
        self._ready_list.append(job)

        self.print('A', job)

        job.cpu.resched()

    def on_terminated(self, job):
        self._ready_list.remove(job)

        self._energy += (job.computation_time *
                self.data["params"]["cpu"].curlvl[3])

        self.print('E', job)

        job.cpu.resched()

    def schedule(self, cpu):
        if self._ready_list:
            # job with the highest priority
            job = min(self._ready_list, key=lambda x: x.period)
            self.print('S', job)
        else:
            job = None

        return (job, cpu)

    def print(self, event, job):
        print("{}\t{}\t{:03.2f}\t{:1.1f}\t{:1.1f}\t{:1.1f}".format(job.name, 
            event, self.sim.now() / self.sim.cycles_per_ms, job.cpu.speed, 
            self.data["params"]["cpu"].curlvl[6], self._energy))

