from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
from enum import Enum
from llist import dllist, dllistnode
import sys
from functools import total_ordering


@total_ordering
class EventType(Enum):
    TERMINATED = 1
    ARRIVAL = 2
    SCHEDULE = 3
    END = 4

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


def simulation(rts, args):
    event_list = dllist()

    for task in rts["ptasks"]:
        insert_event((0, EventType.ARRIVAL, task), event_list)

    end_time = rts["ptasks"][-1]["T"] * args.instance_count
    insert_event((end_time, EventType.END), event_list)

    last_arrival_time = -1

    while event_list:
        node = event_list.first
        v = node.value
        now = v[0]
        if v[1] == EventType.END:
            print("end")
            break
        if v[1] == EventType.ARRIVAL:
            print("{} arrival task {}".format(now, v[2]["nro"]))
            if now > last_arrival_time:
                insert_event((now, EventType.SCHEDULE, v[2]), event_list)
                last_arrival_time = now
            insert_event((now + v[2]["T"], EventType.ARRIVAL, v[2]), event_list)
        if v[1] == EventType.SCHEDULE:
            print("{} schedule".format(now))
        event_list.remove(node)

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
