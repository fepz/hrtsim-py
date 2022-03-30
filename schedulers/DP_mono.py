"""
Dual Priority algorithm for uniprocessor architectures.
"""
from simso.core import Scheduler, Timer
from schedulers.MissedDeadlineException import MissedDeadlineException
from utils.rts import calculate_y


class DP_mono(Scheduler):

    def __init__(self, sim, scheduler_info, **kwargs):
        super().__init__(sim, scheduler_info, **kwargs)
        self.upper_ready_list = []
        self.middle_ready_list = []
        self.lower_ready_list = []
        self.idle_start = 0
        self._sim = sim

    def init(self):
        calculate_y(self.data["params"]["rts"]["ptasks"])
        # Add some extra required fields for dual priority simulation.
        for ptask in self.data["params"]["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0
            ptask["y_counter"] = ptask["y"]

        for atask in self.data["params"]["rts"]["atasks"]:
            atask["start_exec_time"] = 0

    def on_activate(self, job):
        tc = self.sim.now() / self.sim.cycles_per_ms

        if job.task._task_info.task_type == "Periodic":
            job.task.data["y_counter"] = job.task.data["y"]

        print("{0:}\tS\t{1:}\t{2:}\t{3:}\t{4:}".format(tc, job.name.split("_")[0], job.name.split("_")[1], job.name.split("_")[2],
                [task.data["y_counter"] if task._task_info.task_type == "Periodic" else 0 for task in self.task_list]))

        if job.task._task_info.task_type == "Periodic":
            self.lower_ready_list.append(job)
        if job.task._task_info.task_type == "Sporadic":
            self.middle_ready_list.append(job)

        def promotion(job):
            if job in self.lower_ready_list:
                self.lower_ready_list.remove(job)
                self.upper_ready_list.append(job)
                job.cpu.resched()

        if job.task._task_info.task_type == "Periodic":
            t = Timer(self.sim, promotion, [job], job.task.data["y_counter"],  one_shot=True)
            t.start()

        job.cpu.resched()


    def on_terminated(self, job):
        # current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms

        # verify deadline
        if job.exceeded_deadline:
            raise MissedDeadlineException(tc, job)

        # executed time in ms since last execution
        job_runtime = (self.sim.now() - job.task.data["start_exec_time"]) / self.sim.cycles_per_ms

        # decrement promotion times
        for task in self.lower_ready_list:
            if task.data["y_counter"] > 0:
                task.data["y_counter"] -= job_runtime

        job.task.data["y_counter"] = -1

        print("{0:}\tF\t{1:}\t{2:}\t{3:}\t{4:}".format(tc, job.name.split("_")[0], job.name.split("_")[1], job.name.split("_")[2],
                [task.data["y_counter"] if task._task_info.task_type == "Periodic" else 0 for task in self.task_list]))

        # Remove the job from the CPU and reschedule
        if job in self.lower_ready_list:
            self.lower_ready_list.remove(job)
        elif job in self.middle_ready_list:
            self.middle_ready_list.remove(job)
        elif job in self.upper_ready_list:
            self.upper_ready_list.remove(job)

        job.cpu.resched()

    def schedule(self, cpu):
        if cpu.running:
            # current simulation time
            tc = self.sim.now() / self.sim.cycles_per_ms

            # current job executed time in ms
            job_runtime = (self.sim.now() - cpu.running.task.data["start_exec_time"]) / self.sim.cycles_per_ms

            # decrement promotion times
            for task in self.lower_ready_list:
                if task.data["y_counter"] > 0:
                    task.data["y_counter"] -= job_runtime

        if self.upper_ready_list:
            # ready job with the highest priority (lowest period)
            job = min(self.upper_ready_list, key=lambda x: x.period)

            # update execution start time
            job.task.data["start_exec_time"] = self.sim.now()
        elif self.middle_ready_list:
            job = self.middle_ready_list[0]

        elif self.lower_ready_list:
            # ready job with the highest priority (lowest period)
            job = min(self.lower_ready_list, key=lambda x: x.period)

            # update execution start time
            job.task.data["start_exec_time"] = self.sim.now()
        else:
            # idle time start
            self.idle_start = self.sim.now()

            job = None

        return job, cpu
