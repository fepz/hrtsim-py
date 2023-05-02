#!python

from argparse import ArgumentParser, FileType
from utils.files import get_from_file
from utils.rts import mixrange
from schedtests import josephp
from simso.configuration import Configuration
from simso.core import Model
from slack.SlackExceptions import NegativeSlackException, DifferentSlackException
from utils.cpu import Cpu
import sys
import json


class SinkLogger(object):
    """
    Simple logger. Every message is discarded.
    """
    def __init__(self, sim):
        return

    def log(self, msg, kernel=False):
        return

    @property
    def logs(self):
        return


class SinkMonitor(list):
    """
    Simple monitor. Every observation is discarded.
    """
    def __init__(self):
        return

    def observe(self, y,t = None):
        return

    def __len__(self):
        return 0


def create_configuration(rts, instance_count, scheduler):
    """
    TODO: add description
    :param rts:
    :param instance_count:
    :param scheduler:
    :return:
    """
    # Create a SimSo configuration object.
    configuration = Configuration()

    # Simulate until the lower priority periodic task has n instantiations.
    configuration.duration = (rts["ptasks"][-1]["T"] * (instance_count + 1)) * configuration.cycles_per_ms

    # Create the periodic tasks and add them to the SimSo configuration.
    for ptask in rts["ptasks"]:
        configuration.add_task(name="T_{0}".format(int(ptask["nro"])), identifier=int(ptask["nro"]),
                               period=ptask["T"], activation_date=0, deadline=ptask["D"], wcet=ptask["C"],
                               data=ptask)

    # Create the aperiodic tasks and add them to the SimSo configuration.
    for atask in rts["atasks"]:
        configuration.add_task(name="A_{0}".format(int(atask["nro"])), identifier=int(len(rts["ptask"])+atask["nro"]),
                               deadline=1000, wcet=atask["C"], task_type="Sporadic", data=atask,
                               list_activation_dates=[atask["a"]])

    # Add a processor.
    configuration.add_processor(name="CPU 1", identifier=1)

    # Add a scheduler.
    configuration.scheduler_info.clas = scheduler

    # Check the config before trying to run it.
    configuration.check_all()

    return configuration


def run_simulation(rts, args):
    """
    Simulate an rts
    :param rts: task set
    :param args: parameters
    :return: None
    """

    # Evaluate schedulability
    rts["schedulable"] = josephp(rts["ptasks"])[0]

    # Do not simulate if only schedulable systems are required.
    if not rts["schedulable"]:
        if args.only_schedulable:
            return True

    params = {
        "rts": rts,
        "instance_count": args.instance_count,
        "ss_methods": args.ss_methods,
        "scheduler": args.scheduler,
        "gantt": args.gantt,
        "cpu": Cpu(json.load(args.cpu))
    }

    result = {
        "error": False,
    }

    try:
        # Create SimSo configuration.
        cfg = create_configuration(params["rts"], params["instance_count"], params["scheduler"])

        # Creates a SimSo model.
        model = Model(cfg)

        # Parameters needed by the scheduler
        model.scheduler.data = params

        # Discard trace information to reduce memory footprint.
        if not params["gantt"]:
            model._logger = SinkLogger(model)
            for task in model.scheduler.task_list:
                task._monitor = SinkMonitor()
            for cpu in model.scheduler.processors:
                cpu.monitor = SinkMonitor()

        # Run the simulation.
        model.run_model()

    except (NegativeSlackException, DifferentSlackException) as exc:
        result["error"] = True
        result["error_msg"] = str(exc)

    except KeyError as exc:
        result["error"] = True
        result["error_msg"] = "Key not found: {0}.".format(str(exc))

    except (AssertionError, ImportError) as exc:
        result["error"] = True
        result["error_msg"] = str(exc)

    finally:
        if params["gantt"]:
            result["model"] = model

    if result["error"]:
        print("Error: RTS {0}, {1}".format(rts["id"], result["error_msg"]), file=sys.stderr)
        if args.stop_on_error:
            sys.exit(1)

    if args.gantt:
        from gui.gantt import create_gantt_window
        from PyQt5.QtWidgets import QApplication
        app = QApplication(sys.argv)
        ex = create_gantt_window(result["model"])
        app.exec_()

    return result


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


def main():
    # Retrieve command line arguments.
    args = get_args()

    try:
        error = False

        # Simulate the selected rts from the specified file.
        for rts in get_from_file(args.file, mixrange(args.rts)):
            if args.verbose:
                print("Simulating RTS {0:}".format(rts["id"]), file=sys.stderr)
            sim_result = run_simulation(rts, args)
            error |= sim_result["error"]
            if error:
                print("Error: RTS {0}, {1}".format(rts["id"], sim_result["error_msg"]), file=sys.stderr)
                if args.stop_on_error:
                    sys.exit(1)

        if error:
            sys.exit(1)
    except KeyboardInterrupt:
        sys.exit(1)


if __name__ == '__main__':
    main()
