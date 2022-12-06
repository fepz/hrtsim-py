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


class Scheduler:
    def __init__(self):
        self.ready_list = []

    def arrival(self, time, task):
        self.ready_list.append(task)

    def terminated(self, time, task):
        self.ready_list.remove(task)

    def schedule(self, time):
        job = None
        if self.ready_list:
            job = min(self.ready_list, key=lambda x: x["T"])
        return job


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

    sched = Scheduler()

    for task in rts["ptasks"]:
        task["job"] = {"counter": 0, "runtime": task["C"]}
        insert_event(Event(0, EventType.ARRIVAL, task), event_list)

    end_time = rts["ptasks"][-1]["T"] * args.instance_count
    insert_event(Event(end_time, EventType.END, None), event_list)

    last_arrival_time = -1

    while event_list:
        event = event_list.popleft()
        now = event.time

        if event.type == EventType.END:
            break

        if event.type == EventType.ARRIVAL:
            if now > last_arrival_time:
                if not event_list.first.value.type == EventType.SCHEDULE:
                    insert_event(Event(now, EventType.SCHEDULE, None), event_list)
                    last_arrival_time = now
            event.task["job"]["counter"] += 1
            event.task["job"]["runtime"] = event.task["C"]
            insert_event(Event(now + event.task["T"], EventType.ARRIVAL, event.task), event_list)
            sched.arrival(now, event.task)

        if event.type == EventType.TERMINATED:
            sched.terminated(now, event.task)
            insert_event(Event(now, EventType.SCHEDULE, None), event_list)

        if event.type == EventType.SCHEDULE:
            next = event_list.first.value
            job = sched.schedule(now)
            if job:
                print("{}:\t{}".format(now, job))
                if next.time >= now + job["job"]["runtime"]:
                    insert_event(Event(now + job["job"]["runtime"], EventType.TERMINATED, job), event_list)
                else:
                    job["job"]["runtime"] -= next.time - now
            else:
                print("{}:\tempty".format(now))

    print(event_list)


def main():
    # Retrieve command line arguments.
    args = get_args()

    # Simulate the selected rts from the specified file.
    for rts in get_from_file(args.file, mixrange(args.rts)):
        if args.verbose:
            print("Simulating RTS {0:}".format(rts["id"]), file=sys.stderr)
        simulation(rts, args)


if __name__ == '__main__':
    main()
