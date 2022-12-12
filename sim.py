from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
from enum import Enum
from llist import dllist, dllistnode
from math import ceil
from functools import total_ordering
import math
import sys


@total_ordering
class EventType(Enum):
    END = 1
    TERMINATED = 2
    ARRIVAL = 3
    SCHEDULE = 4

    def __ge__(self, other):
        if self.__class__ is other.__class__:
            return self.value >= other.value
        return NotImplemented


class Event:
    def __init__(self, time, type, task):
        self.time = time
        self.type = type
        self.task = task


class Scheduler:
    def __init__(self, configuration):
        self._configuration = configuration

    def arrival(self, time, task):
        pass

    def terminated(self, time, task):
        pass

    def schedule(self, time):
        pass


class LLF_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []

    def arrival(self, time, task):
        self.ready_list.append(task)

    def terminated(self, time, task):
        self.ready_list.remove(task)

    def schedule(self, time):
        job = None
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.job.current_laxity(time))
        return job


class EDF_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []

    def arrival(self, time, task):
        self.ready_list.append(task)

    def terminated(self, time, task):
        self.ready_list.remove(task)

    def schedule(self, time):
        job = None
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.job.absolute_deadline)
        return job


class RM_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []

    def arrival(self, time, task):
        self.ready_list.append(task)

    def terminated(self, time, task):
        self.ready_list.remove(task)

    def schedule(self, time):
        job = None
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.t)
        return job


class RM_SS_mono(Scheduler):
    def __init__(self, configuration):
        super().__init__(configuration)
        self.ready_list = []

    def arrival(self, time, task):
        self.ready_list.append(task)

    def terminated(self, time, task):
        self.ready_list.remove(task)
        # decrement higher priority tasks slack
        reduce_slacks(self._configuration["tasks"][:(task.id - 1)], task.job.runtime, time)
        print(multiple_slack_calc(time, task, self._configuration["tasks"], self._configuration["ss_methods"]))

    def schedule(self, time):
        job = None
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x.t)
        return job


class Job:
    def __init__(self, task, t):
        self._task = task
        self._counter = 0
        self._runtime = task.c
        self._instantiation_time = t

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

    def remaining_runtime(self):
        return self.task.c - self.runtime

    def current_laxity(self, t):
        return self.absolute_deadline - (t + self.task.c)


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
        self._job_counter = 0

    @property
    def id(self):
        return self._id

    @property
    def c(self):
        return self._c

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
    def job(self):
        return self._job

    def new_job(self, t):
        self._job = Job(self, t)
        self._job_counter += 1

    def __str__(self):
        return "Task {}".format(self._id)


def reduce_slacks(tasks, amount, t):
    from math import isclose, fabs
    for task in tasks:
        task.slack -= amount
        if isclose(task.slack, 0, abs_tol=1e-5):
            task.slack = 0
        #if (fabs(task.data["ss"]["slack"] < 0.00005)):
        #    task.data["ss"]["slack"] = 0
        if task.slack < 0:
            #raise NegativeSlackException(t, task, "Scheduler")
            print("negative slack")


def multiple_slack_calc(tc, task, tasks, slack_methods: list) -> dict:
    # calculate slack with each method in slack_methods
    slack_results = [(ss_method.__str__(), ss_method.calculate_slack(task, tasks, tc)) for ss_method in slack_methods]

    # check for negative slacks
    for method, result in slack_results:
        if result["slack"] < 0:
            #raise NegativeSlackException(tc, method, task.job.name if task.job else task.name)
            print("negative slack")

    # verify that all the methods produces the same results
    ss = slack_results[0][1]["slack"]
    ttma = slack_results[0][1]["ttma"]
    for method, result in slack_results:
        if result["slack"] != ss or (result["ttma"] > 0 and result["ttma"] != ttma):
            #raise DifferentSlackException(tc, task.job.name if task.job else task.name, method, slack_results)
            print("different slack")

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

    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def _ceil(self, v):
        return math.ceil(v)

    @cc_counter
    def _floor(self, v):
        return math.floor(v)

    @cc_counter
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
        return {"ceils": self._ceil.counter, "floors": self._floor.counter}


class Fixed2Slack(SlackMethod):

    def __init__(self):
        super().__init__()

    def init(self):
        self._ceil.counter = 0
        self._floor.counter = 0
        self._slack_calc.counter = 0

    def calculate_slack(self, task, task_list, time):
        # theorems and corollaries applied
        theorems = []

        xi = self._ceil(time / task.t) * task.t
        task.di = xi + task.d

        # if it is the max priority task, the slack is trivial
        if task.id == 1:
            return {"slack": task.di - time - task.r, "ttma": task.di, "cc": self._ceil.counter,
                    "theorems": theorems, "interval_length": 0, "slack_calcs": self._slack_calc.counter}

        # sort the task list by period (RM)
        tl = sorted(task_list, key=lambda x: x.t)

        kmax = 0
        tmax = task.di

        # immediate higher priority task
        htask = tl[task.id - 2]

        # corollary 2 (theorem 5)
        if (htask.di + htask.c >= task.di) and (task.di >= htask.ttma):
            theorems.append(5)
            return {"slack": htask.slack - task.c, "ttma": htask.ttma, "cc": self._ceil.counter,
                    "theorems": theorems, "interval_length": 0, "slack_calcs": self._slack_calc.counter}

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

        return {"slack": kmax, "ttma": tmax, "cc": self._ceil.counter + self._floor.counter, "theorems": theorems,
                "interval_length": task.di - intervalo, "slack_calcs": self._slack_calc.counter}


def get_args():
    """ Command line arguments """
    parser = ArgumentParser(description="Simulate a RTS.")
    parser.add_argument("file", nargs='?', type=FileType('r'), default=sys.stdin, help="File with RTS.")
    parser.add_argument("--rts", type=str, help="Which RTS simulate.", default="1")
    parser.add_argument("--scheduler", type=str, help="Scheduling algorithm")
    parser.add_argument("--instance-count", type=int, default=5, help="Stop the simulation after the specified number of instances of the lowest priority task.")
    parser.add_argument("--ss-methods", nargs='+', type=str, help="Slack Stealing methods.")
    parser.add_argument("--only-schedulable", action="store_true", default=False, help="Simulate only schedulable systems.")
    parser.add_argument("--gantt", action="store_true", default=False, help="Show scheduling gantt.")
    parser.add_argument("--stop-on-error", default=False, action="store_true", help="Stop and exit the simulation if an error is detected.")
    parser.add_argument("--verbose", default=False, action="store_true", help="Show progress information on stderr.")
    parser.add_argument("--cpu", type=FileType('r'), help="CPU model.")
    return parser.parse_args()


def insert_event(event, list: dllist):
    tmpnode = None

    for node in list.iternodes():
        if node.value.time >= event.time:
            tmpnode = node
            break

    while tmpnode and tmpnode.value.time == event.time:
        if tmpnode.value.type >= event.type:
            break
        tmpnode = tmpnode.next

    list.insert(event, tmpnode)


def simulation(rts, args):
    event_list = dllist()

    ss_methods = []
    if args.ss_methods:
        for ss_method_name in args.ss_methods:
            ss_methods.append(slack_methods[ss_method_name]())

    for task in rts:
        insert_event(Event(0, EventType.ARRIVAL, task), event_list)

    end_time = rts[-1].t * args.instance_count
    insert_event(Event(end_time, EventType.END, None), event_list)

    scheduler = schedulers[args.scheduler]({"tasks": rts, "ss_methods": ss_methods})

    last_schedule_time = -1

    while event_list:
        event = event_list.popleft()
        now = event.time

        if event.type == EventType.END:
            break

        if event.type == EventType.ARRIVAL:
            if now > last_schedule_time:
                insert_event(Event(now, EventType.SCHEDULE, None), event_list)
                last_schedule_time = now
            event.task.new_job(now)
            insert_event(Event(now + event.task.t, EventType.ARRIVAL, event.task), event_list)
            scheduler.arrival(now, event.task)

        if event.type == EventType.TERMINATED:
            scheduler.terminated(now, event.task)
            insert_event(Event(now, EventType.SCHEDULE, None), event_list)
            last_schedule_time = now

        if event.type == EventType.SCHEDULE:
            next_event = event_list.first.value
            task = scheduler.schedule(now)
            if task:
                print("{}:\t{}".format(now, task))
                if next_event.time >= now + task.job.runtime:
                    insert_event(Event(now + task.job.runtime, EventType.TERMINATED, task), event_list)
                else:
                    task.job.runtime -= next_event.time - now
            else:
                print("{}:\tempty".format(now))


schedulers = {"RM_mono": RM_mono,
              "RM_SS_mono": RM_SS_mono,
              "EDF_mono": EDF_mono,
              "LLF_mono": LLF_mono}


slack_methods = {"Fixed2": Fixed2Slack}


def main():
    # Retrieve command line arguments.
    args = get_args()

    # Simulate the selected rts from the specified file.
    for jrts in get_from_file(args.file, mixrange(args.rts)):
        if args.verbose:
            print("Simulating RTS {0:}".format(jrts["id"]), file=sys.stderr)
        rts = []
        for ptask in jrts["ptasks"]:
            rts.append(Task(ptask))
        rta(rts)
        calculate_k(rts)
        slack = slack_methods["Fixed2"]()
        # Calculate slack at t=0
        for task in rts:
            result = slack.calculate_slack(task, rts, 0)
            task.slack = result["slack"]
            task.ttma = result["ttma"]
        simulation(rts, args)
        print(slack.telemetry())


if __name__ == '__main__':
    main()
