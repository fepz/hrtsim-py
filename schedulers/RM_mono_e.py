"""
Rate Monotic algorithm for uniprocessor architectures with energy consumption.
"""
from simso.core import Scheduler


class RM_mono_e(Scheduler):

    def init(self):
        self._ready_list = []
        self.idle_start = 0
        self._energy = 0
        self._cpu = self.data["params"]["cpu"]
        self._cpu.set_lvl(1.0)

    def on_activate(self, job):
        # compute idle time
        if job.cpu.running is None and self.idle_start > 0:
            elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
            self._energy += elapsed_idle_time * self._cpu.curlvl[3]
            self.idle_start = 0
            self._cpu.set_lvl(1.0)

        self._ready_list.append(job)

        self.print('A', job)

        job.cpu.resched()

    def on_terminated(self, job):
        self._ready_list.remove(job)

        self._energy += job.computation_time * self._cpu.curlvl[3]

        self.print('E', job)

        job.cpu.resched()

    def schedule(self, cpu):
        if self._ready_list:
            # job with the highest priority
            job = min(self._ready_list, key=lambda x: x.period)
            self.print('S', job)
        else:
            # idle time start
            self.idle_start = self.sim.now()
            self._cpu.set_lvl(0)

            job = None

        return (job, cpu)

    def print(self, event, job):
        print("{}\t{}\t{:03.2f}\t{:1.1f}\t{:5.0f}\t{:1.3f}".format(job.name,
                                                                   event, self.sim.now() / self.sim.cycles_per_ms, job.cpu.speed,
                                                                   self._cpu.curlvl[0], self._energy))

