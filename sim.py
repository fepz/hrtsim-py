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
        if node.value[0] >= event[0]:
            tmpnode = node
            break

    while tmpnode and tmpnode.value[0] == event[0]:
        if tmpnode.value[1] >= event[1]:
            break
        tmpnode = tmpnode.next

    list.insert(event, tmpnode)


ready_list = []


def scheduler():
    job = None
    if ready_list:
        job = min(ready_list, key=lambda x: x["T"])
    return job


def simulation(rts, args):
    event_list = dllist()

    for task in rts["ptasks"]:
        task["job"] = {"counter": 0, "runtime": task["C"]}
        insert_event((0, EventType.ARRIVAL, task), event_list)

    end_time = rts["ptasks"][-1]["T"] * args.instance_count
    insert_event((end_time, EventType.END), event_list)

    last_arrival_time = -1

    while event_list:
        v = event_list.popleft()
        now = v[0]

        if v[1] == EventType.END:
            break

        if v[1] == EventType.ARRIVAL:
            if now > last_arrival_time:
                insert_event((now, EventType.SCHEDULE, None), event_list)
                last_arrival_time = now
            v[2]["job"]["counter"] += 1
            v[2]["job"]["runtime"] = v[2]["C"]
            insert_event((now + v[2]["T"], EventType.ARRIVAL, v[2]), event_list)
            ready_list.append(v[2])

        if v[1] == EventType.TERMINATED:
            ready_list.remove(v[2])
            insert_event((now, EventType.SCHEDULE, None), event_list)

        if v[1] == EventType.SCHEDULE:
            next = event_list.first.value
            job = scheduler()
            if job:
                print("{}:\t{}".format(now, job))
                if next[0] >= now + job["job"]["runtime"]:
                    insert_event((now + job["job"]["runtime"], EventType.TERMINATED, job), event_list)
                else:
                    job["job"]["runtime"] -= next[0] - now
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
