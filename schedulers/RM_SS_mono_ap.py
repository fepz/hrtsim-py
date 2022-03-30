"""
Rate Monotic algorithm for uniprocessor architectures -- with Slack Stealing and aperiodic tasks.
"""
from simso.core import Scheduler, Timer
from schedulers.MissedDeadlineException import MissedDeadlineException
from slack.SlackUtils import reduce_slacks, multiple_slack_calc
from utils.rts import calculate_k


class RM_SS_mono_ap(Scheduler):

    def __init__(self, sim, scheduler_info, **kwargs):
        super().__init__(sim, scheduler_info, **kwargs)
        self.ready_list = []
        self.aperiodic_ready_list = []
        self.min_slack = 0
        self.idle_start = 0

    def init(self):
        calculate_k(self.data["params"]["rts"]["ptasks"])

        # Required fields for slack stealing simulation.
        for ptask in self.data["params"]["rts"]["ptasks"]:
            ptask["start_exec_time"] = 0

            ptask["ss"] = {'slack': ptask["k"], 'ttma': 0, 'di': 0, 'start_exec_time': 0, 'last_psi': 0,
                           'last_slack': 0, 'ii': 0}

            for ss_method in self.data["params"]["ss_methods"]:
                ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

        for atask in self.data["params"]["rts"]["atasks"]:
            atask["start_exec_time"] = 0

    def on_activate(self, job):
        periodic_tasks = [task for task in self.task_list if task._task_info.task_type == "Periodic"]

        # compute idle time
        if job.cpu.running is None and self.idle_start > 0:
            elapsed_idle_time = (self.sim.now() - self.idle_start) / self.sim.cycles_per_ms
            t = self.sim.now() / self.sim.cycles_per_ms
            reduce_slacks(periodic_tasks, elapsed_idle_time, t)
            self.idle_start = 0

        if job.task._task_info.task_type == "Periodic":
            self.ready_list.append(job)
        if job.task._task_info.task_type == "Sporadic":
            self.aperiodic_ready_list.append(job)

        tc = self.sim.now() / self.sim.cycles_per_ms
        print("{0:}\tA\t{1:}".format(tc, job.name))

        job.cpu.resched()

    def on_terminated(self, job):
        # current simulation time
        tc = self.sim.now() / self.sim.cycles_per_ms

        # verify deadline
        if job.exceeded_deadline:
            raise MissedDeadlineException(tc, job)

        # executed time in ms since last execution
        job_runtime = (self.sim.now() - job.task.data["start_exec_time"]) / self.sim.cycles_per_ms
            
        periodic_tasks = [task for task in self.task_list if task._task_info.task_type == "Periodic"]

        # decrement higher priority tasks slack
        if job.task._task_info.task_type == "Periodic":
            if self.min_slack > 0:
                reduce_slacks(periodic_tasks[:(job.task.identifier - 1)], job_runtime, tc)
        else:
            if self.min_slack > 0:
                reduce_slacks(periodic_tasks, job_runtime, tc)

        # calculate task slack
        if job.task._task_info.task_type == "Periodic":
            ss_result = multiple_slack_calc(tc, job, periodic_tasks, self.data["ss_methods"])
            job.task.data["ss"]["slack"], job.task.data["ss"]["ttma"] = ss_result["slack"], ss_result["ttma"]

        # print the slack results to stdout
        #for k, v in ss_result["ss_results"]:
        #    print("{0:} {1:} {2:} {3:} {4:} {5:} {6:} {7:}".format(job.name.split("_")[1], job.name.split("_")[2], v["cc"], 
        #        v["interval_length"], v["slack_calcs"], k, v["interval"], " ".join([str(x) for x in v["points"]])))

        # log results
        #if job.task._task_info.task_type == "Periodic":
            #job.task.data["slack"], job.task.data["ttma"] = ss_result["slack"], ss_result["ttma"]

        # Find system new minimum slack
        self.min_slack = min([task.data["ss"]["slack"] for task in self.task_list if task._task_info.task_type == "Periodic"])

        print("{0:}\tF\t{1:}\t{2:}\t{3:}".format(tc, job.name, self.min_slack, [task.data["ss"]["slack"] for task in self.task_list if task._task_info.task_type == "Periodic"]))

        # Remove the job from the CPU and reschedule
        if job in self.ready_list:
            self.ready_list.remove(job)
        elif job in self.aperiodic_ready_list:
            self.aperiodic_ready_list.remove(job)

        job.cpu.resched()

    def schedule(self, cpu):
        if cpu.running:
            # current simulation time
            tc = self.sim.now() / self.sim.cycles_per_ms

            # current job executed time in ms
            job_runtime = (self.sim.now() - cpu.running.task.data["start_exec_time"]) / self.sim.cycles_per_ms

            periodic_tasks = [task for task in self.task_list if task._task_info.task_type == "Periodic"]

            # decrement higher priority tasks slack
            job = cpu.running
            if self.min_slack > 0:
                if job.task._task_info.task_type == "Periodic":
                    reduce_slacks(periodic_tasks[:(job.task.identifier - 1)], job_runtime, tc)
                else:
                    reduce_slacks(periodic_tasks, job_runtime, tc)

            # find system new minimum slack
            self.min_slack = min([task.data["ss"]["slack"] for task in periodic_tasks])

            print("{0:}\tS\t{1:}\t{2:}\t{3:}".format(tc, job.name, self.min_slack, [task.data["ss"]["slack"] for task in periodic_tasks]))

        if self.aperiodic_ready_list and self.min_slack > 0:
            # execute aperiodic task until slack is exhausted or it finishes
            job = self.aperiodic_ready_list[0]

            Timer(self.sim, cpu.resched, [], self.min_slack,  one_shot=True).start()

            # update execution start time
            job.task.data["start_exec_time"] = self.sim.now()
        elif self.ready_list:
            # ready job with the highest priority (lowest period)
            job = min(self.ready_list, key=lambda x: x.period)

            # update execution start time
            job.task.data["start_exec_time"] = self.sim.now()
        else:
            # idle time start
            self.idle_start = self.sim.now()
            job = None

        return job, cpu
