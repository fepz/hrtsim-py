from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
from enum import Enum
from llist import dllist, dllistnode
import sys
from functools import total_ordering


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


class EDF_mono:
    def __init__(self):
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


class RM_mono:
    def __init__(self):
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


class Task:
    def __init__(self, data):
        self._id = data["nro"]
        self._c = data["C"]
        self._t = data["T"]
        self._d = data["D"]
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
    def job(self):
        return self._job

    def new_job(self, t):
        self._job = Job(self, t)
        self._job_counter += 1

    def __str__(self):
        return "Task {}".format(self._id)


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

    scheduler = schedulers[args.scheduler]()

    for task in rts:
        insert_event(Event(0, EventType.ARRIVAL, task), event_list)

    end_time = rts[-1].t * args.instance_count
    insert_event(Event(end_time, EventType.END, None), event_list)

    last_arrival_time = -1
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
              "EDF_mono": EDF_mono}


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
        simulation(rts, args)


if __name__ == '__main__':
    main()
