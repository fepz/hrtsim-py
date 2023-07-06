from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
from utils.cpu import Cpu
from enum import Enum
from pyllist import dllist
from math import ceil, isclose
from sys import maxsize
from functools import total_ordering
import json
import math
import sys


@total_ordering
class EventType(Enum):
    END = 1
    ARRIVAL = 2
    TERMINATED = 3
    SCHEDULE = 4

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class Event:
    def __init__(self, time, type, value):
        self.time = time
        self.type = type
        self.value = value


class Configuration:
    def __init__(self, sim, scheduler, cpu, slack):
        self._sim = sim
        self._scheduler = scheduler
        self._cpu = cpu

    @property
    def sim(self):
        return self._sim

    @property
    def scheduler(self):
        return self._scheduler

    @property
    def cpu(self):
        return self._cpu

    @property
    def slack(self):
        return self._slack


class Scheduler:
    def __init__(self, configuration):
        self._configuration = configuration
        self._energy = 0.0
        self._free = 0.0
        self._leveldvs = 0
        self.current_job = None
        self._slack = 0.0
        self._cpu = configuration["cpu"]

    def arrival(self, time, task):
        pass

    def terminated(self, time, job):
        pass

    def schedule(self, time):
        pass

    @property
    def energy(self):
        return self._energy

    @energy.setter
    def energy(self, energy):
        self._energy = energy

    @property
    def free(self):
        return self._free

    @free.setter
    def free(self, free):
        self._free = free

    @property
    def slack(self):
        return self._slack

    @slack.setter
    def slack(self, slack):
        self._slack = slack

    @property
    def cpu(self):
        return self._cpu

    @cpu.setter
    def cpu(self, cpu):
        self._cpu = cpu


class LLF_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []
        self.current_job = None
        self.last_schedule_time = 0
        self.idle = False

    def arrival(self, time, task):
        self.ready_list.append(task.new_job(time))

    def terminated(self, time, job):
        if time > job.absolute_deadline:
            print("{} missed deadline at {:5.3f}".format(job, job.absolute_deadline), file=sys.stderr)
            exit(1)
        slice = time - self.last_schedule_time
        job.runtime += slice
        self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        self.ready_list.remove(job)
        self.current_job = None

    def schedule(self, time):
        job = None
        slice = time - self.last_schedule_time
        self.last_schedule_time = time
        if self.current_job:
            self.current_job.runtime += slice
            self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.current_laxity(time))
            self.current_job = job
            self.idle = False
        else:
            self.current_job = None
            self.idle = True
        return job, 0, job.task.c - job.runtime if job else 0


class EDF_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []
        self.current_job = None
        self.last_schedule_time = 0
        self.idle = False

    def arrival(self, time, task):
        self.ready_list.append(task.new_job(time))

    def terminated(self, time, job):
        if time > job.absolute_deadline:
            print("{} missed deadline at {:5.3f}".format(job, job.absolute_deadline), file=sys.stderr)
            exit(1)
        slice = time - self.last_schedule_time
        job.runtime += slice
        self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        self.ready_list.remove(job)
        self.current_job = None

    def schedule(self, time):
        job = None
        slice = time - self.last_schedule_time
        self.last_schedule_time = time
        if self.current_job:
            self.current_job.runtime += slice
            self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.absolute_deadline)
            self.current_job = job
            self.idle = False
        else:
            self.current_job = None
            self.idle = True
        return job, 0, job.task.c - job.runtime if job else 0


class RM_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []
        self.current_job = None
        self.last_schedule_time = 0
        self.idle = False
        self.slack = 0

    def arrival(self, time, task):
        self.ready_list.append(task.new_job(time))

    def terminated(self, time, job):
        if time > job.absolute_deadline:
            print("{} missed deadline at {:5.3f}".format(job, job.absolute_deadline), file=sys.stderr)
            exit(1)
        slice = time - self.last_schedule_time
        job.runtime += slice
        self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        self.ready_list.remove(job)
        self.current_job = None

    def schedule(self, time):
        job = None
        slice = time - self.last_schedule_time
        self.last_schedule_time = time
        if self.current_job:
            self.current_job.runtime += slice
            self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.task.t)
            self.current_job = job
            self.idle = False
        else:
            self.current_job = None
            self.idle = True
        return job, 0, job.task.c - job.runtime if job else 0


class RM_SS_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []
        self.current_job = None
        self.last_schedule_time = 0
        self.slack = 0.0
        self.idle = False
        self.tasks = configuration["tasks"]
        self.f_min = 1.0

        # Calculate slack at t=0
        for task in self.tasks:
            result = slack_calc(0, task, self.tasks, self._configuration["ss_methods"])
            task.slack = result["slack"]
            task.ttma = result["ttma"]

        self.slack, self.slack_time, self.slack_task = get_minimum_slack(self.tasks)

    def arrival(self, time, task):
        self.ready_list.append(task.new_job(time))

    def terminated(self, time, job):
        if time > job.absolute_deadline:
            print("{} missed deadline at {:5.3f}".format(job, job.absolute_deadline), file=sys.stderr)
            exit(1)
        slice = time - self.last_schedule_time
        job.runtime += slice
        self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
        self.ready_list.remove(job)
        self.current_job = None
        # decrement higher priority tasks slack
        reduce_slacks(self._configuration["tasks"][:(job.task.id - 1)], slice, time)
        # calculate slack
        result = slack_calc(time, job.task, self._configuration["tasks"], self._configuration["ss_methods"])
        job.task.slack = result["slack"]
        job.task.ttma = result["ttma"]

    def schedule(self, time):
        job = None
        slice = time - self.last_schedule_time
        self.last_schedule_time = time
        if self.current_job:
            self.current_job.runtime += slice
            self.energy = self.energy + (slice * self.cpu.lvls[-1][3])
            reduce_slacks(self._configuration["tasks"][:(self.current_job.task.id - 1)], slice, time)
        else:
            if self.idle:
                reduce_slacks(self._configuration["tasks"], slice, time)

        self.slack, self.min_slack_time, self.min_slack_task = get_minimum_slack(self._configuration["tasks"])

        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.task.t)
            self.current_job = job
            self.idle = False
        else:
            self.current_job = None
            self.idle = True
        return job, 0, job.task.c - job.runtime if job else 0


class LPFPS(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []
        self.current_job = None
        self.last_schedule_time = 0
        self.idle = False
        self.slack = 0
        self.cpu_lvl = self.cpu.lvls[-1]

    def arrival(self, time, task):
        self.ready_list.append(task.new_job(time))

    def terminated(self, time, job):
        slice = time - self.last_schedule_time
        job.runtime += slice
        self.ready_list.remove(job)
        self.current_job = None
        self.energy = self.energy + (slice * self.cpu_lvl[3])
        self.cpu_lvl = self.cpu.lvls[-1]

    def schedule(self, time):
        job = None
        slice = time - self.last_schedule_time
        self.last_schedule_time = time
        if self.current_job:
            self.energy = self.energy + (slice * self.cpu_lvl[3])
            self.current_job.runtime += slice
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.task.t)
            job.b = job.runtime_left()
            if len(self.ready_list) == 1:
                # Compute new speed ratio
                ratio = job.runtime_left() / (self._configuration["sim"].next_arrival() - time)
                if ratio < 1.0:
                    self.cpu_lvl = self._get_cpu_level(ratio)[0]
                    job.b = job.b * self.cpu_lvl[6]
            self.current_job = job
            self.idle = False
        else:
            self.current_job = None
            self.idle = True
        return job, 0, job.b if job else 0

    def _get_cpu_level(self, ratio):
        for i, lvl in enumerate(self.cpu.lvls[1:], start=1):
            if lvl[6] >= ratio:
                return lvl, self.cpu.lvls[i - 1]


class RM_SS_mono_e(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []
        self.current_job = None
        self.last_schedule_time = 0
        self.idle = False
        self.energy = 0
        self.tasks = configuration["tasks"]
        self.cpu_lvlz = None
        self.icf_task = None
        self.icf_time = 0

        # Found the minimum V/F level in which the periodic tasks are schedulable.
        for lvl in self.cpu.lvls:
            if rta(self.tasks, lvl[5]):
                self.cpu_lvlz = lvl
                break
        else:
            print("No schedulable.", file=sys.stderr)
            sys.exit(1)

        # Initial CPU v/f level
        self.f_min = self.cpu_lvlz[6]
        self.cpu.set_lvl(self.cpu_lvlz[6])

        # Update the WCET of each task
        for task in self.tasks:
            task.c = task.c * self.cpu_lvlz[5]
            task.a = task.c

        # Calculate slack at t=0
        for task in self.tasks:
            result = slack_calc(0, task, self.tasks, self._configuration["ss_methods"])
            task.slack = result["slack"]
            task.ttma = result["ttma"]

        self.slack, self.slack_time, self.slack_task = get_minimum_slack(self.tasks)

    def arrival(self, time, task):
        job = task.new_job(time)
        job.leveldvs = self.cpu_lvlz
        self.ready_list.append(job)

    def terminated(self, time, job):
        if time > job.absolute_deadline:
            print("{} missed deadline at {:5.3f}".format(job, job.absolute_deadline), file=sys.stderr)
            exit(1)
        self.current_job = None
        self.ready_list.remove(job)
        time_slice = time - self.last_schedule_time
        job.runtime += time_slice
        self.energy = self.energy + (time_slice * job.leveldvs[3])
        # decrement higher priority tasks slack
        reduce_slacks(self.tasks[:job.task.id - 1], time_slice, time)
        if job.b > job.b_temp:
            reduce_slacks(self.tasks[job.task.id:], job.b - job.b_temp, time)
        # calculate slack
        result = slack_calc(time, job.task, self.tasks, self._configuration["ss_methods"])
        job.task.slack = result["slack"]
        job.task.ttma = result["ttma"]

    def schedule(self, time):
        time_slice = time - self.last_schedule_time
        next_stop = self._configuration["sim"].next_arrival()
        self.last_schedule_time = time

        if self.current_job:
            self.current_job.runtime += time_slice
            reduce_slacks(self.tasks[:self.current_job.task.id - 1], time_slice, time)
            if self.current_job.b > self.current_job.b_temp:
                reduce_slacks(self.tasks[self.current_job.task.id - 1:], self.current_job.b - self.current_job.b_temp, time)
            self.current_job.b -= time_slice
            self.energy = self.energy + (time_slice * self.current_job.leveldvs[3])
        else:
            if self.idle:
                reduce_slacks(self.tasks, time_slice, time)
                self.free += time_slice
                self.idle = False

        self.slack, self.slack_time, self.slack_task = get_minimum_slack(self.tasks)

        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.task.t)

            if self.slack == 0:
                self.current_job = job
                return job, 0, job.b

            self.current_job = job

            return self._new_runtime(job, time, next_stop)
        else:
            self.current_job = None
            self.idle = True

        return self.current_job, 0, 0

    def _new_runtime(self, job, time, next_stop):
        runtime = job.b
        job.b_temp = job.b

        error = 0.1e-5

        if math.isclose(job.b, job.task.c):
            leveldvs = job.leveldvs
            b = job.b
            if (next_stop - time - job.task.c > error) and (len(self.ready_list) == 1):
                self.f_ideal = job.task.c / (next_stop - time) * self.cpu_lvlz[6]
                i, l = self.cpu.get_lvl_idx(self.f_ideal)
                for lvl in self.cpu.lvls[i:]:
                    b = job.task.c * (self.cpu_lvlz[0] / lvl[0])
                    if b - job.task.c - self.slack <= error:
                        break
                if isclose(job.absolute_deadline, next_stop):
                    pass
                else:
                    self._slackb = job.task.c * self.slack / (self.slack_time - time - self.slack)
            else:
                if self.icf_task != self.slack_task or self.icf_time != self.slack_time:
                    self.f_ideal = ((self.slack_time - time - self.slack) / (self.slack_time - time)) * \
                                   self.cpu_lvlz[6]
                    self.icf_task = self.slack_task
                    self.icf_time = self.slack_time
                    # level p-1 and p
                    self._cpu_level_p1, self._cpu_level_p = self.cpu.get_adjacent_lvls(self.f_ideal)
                    self._slacksob = (self.slack_time - time) * (1 - (self.f_ideal / self._cpu_level_p1[6]))
                    self._slackb = job.task.c * self.slack / (self.slack_time - time - self.slack)

                b = job.task.c * (self.cpu_lvlz[0] / self._cpu_level_p[0])

                leveldvs = job.leveldvs
                if (b - job.task.c - self._slacksob - self._slackb > error) or (b - job.task.c - self.slack > error):
                    i, l = self.cpu.get_lvl_idx(self.f_ideal)
                    for lvl in self.cpu.lvls[i + 1:]:
                        b = job.task.c * (self.cpu_lvlz[0] / lvl[0])
                        if b - job.task.c - self.slack <= error:
                            leveldvs = lvl
                            break
                else:
                    self._slacksob -= (b - job.task.c * (self.cpu_lvlz[0] / self._cpu_level_p1[0]))
                    leveldvs = self._cpu_level_p

            if leveldvs[0] < job.leveldvs[0]:
                job.b = b
                job.leveldvs = leveldvs
        else:
            if next_stop - (time + runtime) > error and len(self.ready_list) == 1 and (job.absolute_deadline - next_stop) < error:
                self.f_ideal = runtime / (next_stop - time) * job.leveldvs[6]
                i, l = self.cpu.get_lvl_idx(self.f_ideal)
                for lvl in self.cpu.lvls[i + 1:]:
                    b = runtime * (self.cpu_lvlz[0] / lvl[0])
                    if b - (runtime + self.slack) < error and abs(b - job.task.c - self.slack) < error:
                        if lvl[0] < job.leveldvs[0]:
                            job.b = b
                            job.leveldvs = lvl
                            break
            else:
                self.f_ideal = ((self.slack_time - time - self.slack) / (self.slack_time - time)) * self.cpu_lvlz[6]
                # level p-1 and p
                self._cpu_level_p1, self._cpu_level_p = self.cpu.get_adjacent_lvls(self.f_ideal)
                self._slacksob = (self.slack_time - time) * (1 - (self.f_ideal / self._cpu_level_p1[6]))
                self._slackb = runtime * self.slack / (self.slack_time - time - self.slack)

                job.b = runtime * (job.leveldvs[0] / self._cpu_level_p[0])

                if (job.b - runtime - self._slacksob - self._slackb > error) or (job.b - runtime - self.slack > error):
                    i, l = self.cpu.get_lvl_idx(self.f_ideal)
                    for lvl in self.cpu.lvls[i + 1:]:
                        b = runtime * (job.leveldvs[0] / lvl[0])
                        if b - runtime - self.slack < error:
                            job.b = b
                            job.leveldvs = lvl
                            break
                else:
                    self._slacksob -= (job.b - runtime * (job.leveldvs[0] / self._cpu_level_p1[0]))
                    job.leveldvs = self._cpu_level_p

        return job, job.b - job.b_temp, job.b_temp


class Job:
    def __init__(self, task, t, id):
        self._task = task
        self._id = id
        self._counter = 0
        self._runtime = 0
        self._instantiation_time = t
        self._b = task.c
        self._b_temp = self._b
        self._leveldvs = None

    @property
    def instantiation_time(self):
        return self._instantiation_time

    @property
    def absolute_deadline(self):
        return self._instantiation_time + self._task.d

    @property
    def task(self):
        return self._task

    @property
    def runtime(self):
        return self._runtime

    @runtime.setter
    def runtime(self, runtime):
        self._runtime = runtime

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, b):
        self._b = b

    @property
    def b_temp(self):
        return self._b_temp

    @b_temp.setter
    def b_temp(self, b_temp):
        self._b_temp = b_temp
    @property
    def leveldvs(self):
        return self._leveldvs

    @leveldvs.setter
    def leveldvs(self, leveldvs):
        self._leveldvs = leveldvs

    def runtime_left(self):
        return self.task.c - self.runtime

    def current_laxity(self, t):
        return self.absolute_deadline - (t + self.task.c)

    def __str__(self):
        return "{}_{}".format(self.task, self._id)


class Task:
    def __init__(self, data):
        self._id = data["nro"]
        self._c = data["C"]
        self._t = data["T"]
        self._d = data["D"]
        self._r = 0
        self._k = 0
        self._y = 0
        self._a = self._c
        self._b = self._t
        self._di = 0
        self._ttma = 0
        self._job = None
        self._last_job = None
        self._job_counter = 0
        self._slack = 0
        self._ss = {}

    @property
    def id(self):
        return self._id

    @property
    def c(self):
        return self._c

    @c.setter
    def c(self, c):
        self._c = c

    @property
    def t(self):
        return self._t

    @property
    def d(self):
        return self._d

    @property
    def k(self):
        return self._k

    @k.setter
    def k(self, k):
        self._k = k

    @property
    def r(self):
        return self._r

    @r.setter
    def r(self, r):
        self._r = r

    @property
    def y(self):
        return self._d - self._r

    @property
    def a(self):
        return self._a

    @a.setter
    def a(self, a):
        self._a = a

    @property
    def b(self):
        return self._b

    @b.setter
    def b(self, b):
        self._b = b

    @property
    def di(self):
        return self._di

    @di.setter
    def di(self, di):
        self._di = di

    @property
    def ttma(self):
        return self._ttma

    @ttma.setter
    def ttma(self, ttma):
        self._ttma = ttma

    @property
    def laxity(self):
        return self._d - self._c

    @property
    def slack(self):
        return self._slack

    @slack.setter
    def slack(self, slack):
        self._slack = slack

    @property
    def ss(self):
        return self._ss;

    @property
    def job(self):
        return self._job

    def new_job(self, t):
        self._job_counter += 1
        self._job = Job(self, t, self._job_counter)
        return self._job

    def end_job(self):
        self._last_job = self._job
        self._job = None

    def __str__(self):
        return "T_{}".format(self._id)


class Rts:
    def __init__(self, tasks):
        self._ptasks = [Task(ptask) for ptask in tasks["ptasks"]]
        self._schedulable = rta(self.ptasks)

    @property
    def ptasks(self):
        return self._ptasks

    @property
    def schedulable(self):
        return self._schedulable


def get_minimum_slack(tasks: list):
    """ Find the system minimum slack and the time at which it occurs """

    _min_slack = maxsize
    _min_slack_t = 0
    _min_slack_task = None

    for task in tasks:
        if isclose(task.slack, _min_slack) or _min_slack > task.slack:
            _min_slack = task.slack
            _min_slack_t = task.ttma
            _min_slack_task = task

    return _min_slack, _min_slack_t, _min_slack_task


def reduce_slacks(tasks, amount, t):
    for task in tasks:
        task.slack -= amount
        if isclose(task.slack, 0, abs_tol=1e-5):
            task.slack = 0
        if task.slack < 0:
            print("reduce_slacks: negative slack", file=sys.stderr)
            print("t={}, task={}, amount={}".format(t, task, amount), file=sys.stderr)
            print(["{:03.3f}".format(task.slack) for task in tasks], file=sys.stderr)
            exit(1)


def slack_calc(tc: float, task: Task, tasks: list, slack_methods: list) -> dict:
    # calculate slack with each method in slack_methods
    slack_results = [(ss_method.__str__(), ss_method.calculate_slack(task, tasks, tc)) for ss_method in slack_methods]

    # check for negative slacks
    for method, result in slack_results:
        if result["slack"] < 0:
            print("slack_calc: negative slack", file=sys.stderr)
            exit(1)

    # verify that all the methods produces the same results
    ss = slack_results[0][1]["slack"]
    ttma = slack_results[0][1]["ttma"]
    for method, result in slack_results:
        if result["slack"] != ss or (result["ttma"] > 0 and result["ttma"] != ttma):
            print("slack_calc: slack mismatch", file=sys.stderr)
            exit(1)

    # return slack and ttma
    return {"slack": ss, "ttma": ttma, "ss_results": slack_results}


def calculate_k(rts: list, vf=1.0) -> None:
    """ Calcula el K de cada tarea (maximo retraso en el instante critico) """
    rts[0].k = rts[0].t - (rts[0].c * vf)

    for i, task in enumerate(rts[1:], 1):
        t = 0
        k = 1
        while t <= task.d:
            w = k + (task.c*vf) + sum([ceil(float(t) / float(taskp.t))*(taskp.c*vf) for taskp in rts[:i]])
            if t == w:
                k += 1
            t = w
        task.k = k - 1


def rta(rts: list, vf=1.0) -> bool:
    schedulable = True

    t = rts[0].c * vf
    rts[0].r = rts[0].c * vf

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + (task.c * vf)

        while schedulable:
            t = t_mas
            w = task.c * vf

            for jdx, jtask in enumerate(rts[:idx]):
                w += ceil(t_mas / jtask.t) * (jtask.c * vf)
                if w > task.d:
                    schedulable = False
                    break

            t_mas = w
            if t == t_mas:
                task.r = t
                break

        if not schedulable:
            break

    return schedulable


class SlackMethod:
    def __init__(self):
        self._ceil_counter = 0
        self._floor_counter = 0

    def _ceil(self, v):
        self._ceil_counter += 1
        return math.ceil(v)

    def _floor(self, v):
        self._floor_counter += 1
        return math.floor(v)

    def _slack_calc(self, task_list, tc, t, wc):
        w = 0
        for task in task_list:
            b = task.b
            if (t > b) or (t <= (b - task.t)):
                a_t = self._ceil(t / task.t)
                task.a = a_t * task.c
                task.b = a_t * task.t
            w += task.a
        return t - tc - w + wc, w

    def calculate_slack(self, task, task_list, time):
        pass

    def telemetry(self):
        return {"ceils": self._ceil_counter, "floors": self._floor_counter}


class Fast2Slack(SlackMethod):
    def __init__(self):
        super().__init__()

    def _loop(self, di, t1, tasks):
        t1_tmp = t1
        w = 0

        for task in reversed(tasks):
            tss = task.ss["Fast2"]
            if (t1_tmp <= tss["b"] - task.period) or (tss["b"] < t1_tmp):
                _ceil = ceil(t1_tmp / task.t)
                ceil_a = _ceil * task.c
                ceil_b = _ceil * task.period

                if ceil_a > tss["a"]:
                    t1_tmp += ceil_a - tss["a"]
                    if t1_tmp > di:
                        break

                tss["a"] = ceil_a
                tss["b"] = ceil_b

            w = w + tss["a"]

        return w, t1_tmp

    def _heuristic(self, tc, wc, tmas, tmax, smax, tasks):
        di = tasks[-1].di
        tmin = di
        points = []

        for task in tasks[:-1]:
            tss = task.ss["Fast2"]
            b = tss["b"]

            if tmas <= (b - task.t):
                tss["a"] -= task.c
                tss["b"] -= task.t
                b = tss["b"]

            if b < tmin:
                tmin = b

            if tmas <= b < di:
                if tss["c"] != b:
                    slack_tmp = self._slackcalc(tasks, tc, b, wc)
                    points.append(b)

                    if slack_tmp > smax:
                        smax = slack_tmp
                        tmax = b
                    else:
                        if slack_tmp == smax:
                            if tmax > b:
                                tmax = b

                    tss["c"] = b

        return tmin, tmax, smax, points

    def calculate_slack(self, task, task_list, time):
        # collects the instants at which the slack is calculated
        ss_points = []

        # theorems and corollaries applied
        theorems = []

        xi = ceil(time / task.c) * task.c
        task.di = xi + task.d

        # if it is the max priority task, the slack is trivial
        if task.id == 1:
            return {"slack": task.di - time - task.r, "ttma": task.di, "cc": self._ceil_counter,
                    "theorems": theorems, "interval_length": 0}

        # sort the task list by period (RM)
        tl = sorted(task_list, key=lambda x: x.t)

        kmax = task.k
        tmax = task.di

        # immediate higher priority task
        htask = tl[task.id - 2]

        htask_wcet = htask.c
        task_wcet = task.c

        # corollary 5 (theorem 13) for RM
        if htask.di + htask_wcet >= task.di >= htask.ttma:
            return {"slack": task.slack - task_wcet, "ttma": task.ttma, "cc": self._ceil_counter,
                    "theorems": [5], "interval_length": 0}

        # theorem 10
        interval = task.di - task.r + task_wcet

        # workload at tc
        wc = 0
        for task in tl[:task.id]:
            a = self._floor(time / task.d)
            wc += (a * task.c)
            if task.job and task.job.runtime > 0:
                wc += task.c

        # corollary 4 (theorem 12) for RM
        if interval <= (htask.di + htask_wcet) < task.di:
            interval = htask.di + htask_wcet

            # new initial values for kmax and tmax
            if kmax < htask.slack - task_wcet:
                kmax = htask.slack - task_wcet
                tmax = htask.ttma

            theorems.append(12)

        # calculate slack in deadline
        s, _ = self._slack_calc(tl[:task.id], time, task.di, wc)
        ss_points.append(task.di)

        if s >= kmax:
            if s == kmax:
                if tmax > task.di:
                    tmax = task.di
            else:
                tmax = task.di
            kmax = s

        # use the max slack as initial value
        s = kmax

        t1 = t = interval

        # higher priority tasks
        for htask in tl[:task.id - 1]:
            htask.c = 0

        # epsilon
        e = 5 * 0.0000001

        # iterative section
        while t < task.di:
            w, t1 = self._loop(task.di, t1, tl[:task.id])

            if t1 > task.di:
                break

            tmas = time + s + w - wc

            if t == tmas:
                if tmax == tmas:
                    # fixed point previously found
                    t += e
                    s += e
                else:
                    # this is a new fixed point
                    if tmax > tmas:
                        tmax = tmas

                    tmax_arg = tmax
                    tmin, tmax, s, points = self._heuristic(time, wc, tmas, tmax, kmax, tl[:task.id])
                    # print("{0:}\tFast2\t{1:} {2:} {3:} {4:} = _heuristic(tc, wc, tmas, tmax={5:}, kmax, tasks)".format(task.job.name, tmin, tmax, s, points, tmax_arg))
                    ss_points.extend(points)

                    kmax = s

                    if t == tmax:
                        s += e

                    t = tmin + e

                t1 = t
            else:
                if t > tmas:
                    s += t - tmas
                else:
                    if tmas > t1:
                        t1 = tmas
                    t = tmas

        return {"slack": kmax, "ttma": tmax, "cc": self._ceil_counter + self._floor_counter, "theorems": theorems}


class Fixed2Slack(SlackMethod):
    def __init__(self):
        super().__init__()

    def calculate_slack(self, task, task_list, time):
        # theorems and corollaries applied
        theorems = []

        xi = self._ceil(time / task.t) * task.t
        task.di = xi + task.d

        # if it is the max priority task, the slack is trivial
        if task.id == 1:
            return {"slack": task.di - time - task.r, "ttma": task.di, "cc": self._ceil_counter,
                    "theorems": theorems, "interval_length": 0}

        # sort the task list by period (RM)
        tl = sorted(task_list, key=lambda x: x.t)

        kmax = 0
        tmax = task.di

        # immediate higher priority task
        htask = tl[task.id - 2]

        # corollary 2 (theorem 5)
        if (htask.di + htask.c >= task.di) and (task.di >= htask.ttma):
            theorems.append(5)
            return {"slack": htask.slack - task.c, "ttma": htask.ttma, "cc": self._ceil_counter,
                    "theorems": theorems, "interval_length": 0}

        # theorem 3
        intervalo = xi + (task.d - task.r) + task.c

        # corollary 1 (theorem 4)
        if intervalo <= (htask.di + htask.c) <= task.di:
            intervalo = htask.di + htask.c
            tmax = htask.ttma
            kmax = htask.slack - task.c
            theorems.append(4)

        # workload at t
        wc = 0
        for task in tl[:task.id]:
            a = self._floor(time / task.d)
            wc += (a * task.c)
            if task.job and task.job.runtime > 0:
                wc += task.c

        # calculate slack in deadline
        k2, w = self._slack_calc(tl[:task.id], time, task.di, wc)

        # update kmax and tmax if the slack at the deadline is bigger
        if k2 >= kmax:
            if k2 == kmax:
                if tmax > task.di:
                    tmax = task.di
            else:
                tmax = task.di
            kmax = k2

        # calculate slack at arrival time of higher priority tasks
        for htask in tl[:(task.id - 1)]:
            ii = self._ceil(intervalo / htask.t) * htask.t

            while ii < task.di:
                k2, w = self._slack_calc(tl[:task.id], time, ii, wc)

                # update kmax and tmax if a greater slack value was found
                if k2 > kmax:
                    tmax = ii
                    kmax = k2
                else:
                    if k2 == kmax:
                        if tmax > ii:
                            tmax = ii

                # next arrival
                ii += htask.t

        return {"slack": kmax, "ttma": tmax, "cc": self._ceil_counter + self._floor_counter, "theorems": theorems,
                "interval_length": task.di - intervalo}


class Simulator:
    def __init__(self, rts, args):
        self._event_list = dllist()
        self._rts = rts
        self._args = args

        for task in self._rts.ptasks:
            self.insert_event(Event(0, EventType.ARRIVAL, task))

        self._ss_methods = [slack_methods[ss]() for ss in args.ss_methods]

        #end_time = self._rts.ptasks[-1].t * args.instance_count
        end_time = args.end
        self.insert_event(Event(end_time, EventType.END, None))

        self._cpu = Cpu(json.load(args.cpu)) if args.cpu else None

        self._scheduler = schedulers[args.scheduler]({"sim": self, "tasks": self._rts.ptasks, "ss_methods": self._ss_methods, "cpu": self._cpu})
        self._last_schedule_time = -1

    def insert_event(self, event):
        tmpnode = None

        for node in self._event_list.iternodes():
            if node.value.time >= event.time:
                tmpnode = node
                break

        while tmpnode and tmpnode.value.time == event.time:
            if tmpnode.value.type >= event.type:
                break
            tmpnode = tmpnode.next

        self._event_list.insert(event, tmpnode)

    def sim(self):
        np_flag = False
        np_flag_sched = False
        np = 0
        while self._event_list:
            event = self._event_list.popleft()
            now = event.time

            if event.type == EventType.END:
                break

            if event.type == EventType.ARRIVAL:
                task = event.value
                self.insert_event(Event(now + task.t, EventType.ARRIVAL, task))
                self._scheduler.arrival(now, task)
                if np_flag:
                    if not np_flag_sched:
                        self.insert_event(Event(self._last_schedule_time + np, EventType.SCHEDULE, None))
                        self._last_schedule_time = self._last_schedule_time + np
                        np_flag_sched = True
                else:
                    if now > self._last_schedule_time:
                        self._last_schedule_time = now
                        self.insert_event(Event(now, EventType.SCHEDULE, None))

            if event.type == EventType.TERMINATED:
                job = event.value
                self._scheduler.terminated(now, job)
                if now > self._last_schedule_time:
                    self.insert_event(Event(now, EventType.SCHEDULE, None))
                    self._last_schedule_time = now

            if event.type == EventType.SCHEDULE:
                next_event = self._event_list.first.value
                decision = self._scheduler.schedule(now)
                np_flag = False
                np = 0
                job = decision[0]
                if job:
                    slice = decision[1] + decision[2]
                    if ((now + slice) - next_event.time) <= 0.1e-5:
                        event_time = now + slice
                        if abs(now + slice - next_event.time) < 0.1e-5:
                            event_time = next_event.time
                        self.insert_event(Event(event_time, EventType.TERMINATED, job))
                    elif ((now + decision[1]) - next_event.time) <= 0.1e-5:
                        pass
                    else:
                        np_flag = True
                        np_flag_sched = False
                        np = decision[1]

                if not self._args.silent:
                    print("{:5.3f}\t{}\t{:.3f}\t{}\t{:.3f}\t{:.3f}".format(now, str(job if job else "E").rjust(10, ' '),
                                                    self._scheduler.slack, "\t".join(["{:03.3f}".format(task.slack) for task in self._rts.ptasks]),
                                                    self._scheduler.current_job.leveldvs[6] if self._scheduler.current_job else 0,
                                                    self._scheduler.energy))

        for ss_method in self._ss_methods:
            print("{}: {}".format(ss_method.__class__.__name__, ss_method.telemetry()))
        print("{}".format(self._scheduler.energy))
        print("{}".format(self._scheduler.free / now))
        print("{}".format(self._scheduler.f_min))

    def next_arrival(self):
        return self._event_list.first.value.time


schedulers = {"RM_mono": RM_mono,
              "RM_SS_mono": RM_SS_mono,
              "RM_SS_mono_e": RM_SS_mono_e,
              "EDF_mono": EDF_mono,
              "LLF_mono": LLF_mono,
              "LPFPS": LPFPS}


slack_methods = {"Fixed2": Fixed2Slack,
                 "Fast2": Fast2Slack}


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Simulate a RTS.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="Which RTS simulate.", default="1")
    parser.add_argument("--scheduler", type=str, help="Scheduling algorithm")
    parser.add_argument("--instance-count", type=int, default=5, help="Stop the simulation after the specified number of instances of the lowest priority task.")
    parser.add_argument("--end", type=int, default=100, help="Stop the simulation at this instant.")
    parser.add_argument("--ss-methods", nargs='+', type=str, help="Slack Stealing methods.")
    parser.add_argument("--only-schedulable", action="store_true", default=False, help="Simulate only schedulable systems.")
    parser.add_argument("--gantt", action="store_true", default=False, help="Show scheduling gantt.")
    parser.add_argument("--stop-on-error", default=False, action="store_true", help="Stop and exit the simulation if an error is detected.")
    parser.add_argument("--verbose", default=False, action="store_true", help="Show progress information on stderr.")
    parser.add_argument("--cpu", type=FileType('r'), help="CPU model.")
    parser.add_argument("--silent", action="store_true", default=False, help="Do not show scheduling output.")
    return parser.parse_args()


def main():
    # Retrieve command line arguments.
    args = get_args()

    # Simulate the selected rts from the specified file.
    for rts in get_from_file(args.file, mixrange(args.rts)):
        if args.verbose:
            print("Simulating RTS {0:}".format(rts["id"]), file=sys.stderr)
        sim = Simulator(Rts(rts), args)
        sim.sim()


if __name__ == '__main__':
    main()
