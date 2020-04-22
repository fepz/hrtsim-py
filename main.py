from argparse import ArgumentParser
from collections import defaultdict
from tkinter import Tk

from simso.core import JobEvent

from gui.maingui import MainGui
from resources.xml import load_from_xml
from schedulers.slack import SlackEvent
from simulations.slack.simslack import create_configuration, create_model
from slack.SlackExceptions import NegativeSlackException
from slack.SlackFixed import SlackFixed
from rta.rta3 import rta3


def results(model, configuration, njobs):
    # Cycles per ms used by the model (defaults to 1000000)
    cycles_per_ms = configuration.cycles_per_ms

    task_first_exec = defaultdict(list)
    task_slack_cc = defaultdict(list)

    # Collect the activation, start execution and termination of the first ntask jobs for each task
    for task in model.task_list:
        activate_flag = False
        executed_time = 0.0
        job_count = 0

        for evt in task.monitor:
            if evt[1].event == JobEvent.ACTIVATE:
                activate_flag = True

            if evt[1].event == JobEvent.EXECUTE:
                # If it is the first execution after activation, record the event time
                if activate_flag:
                    executed_time = evt[0]
                    activate_flag = False

            if isinstance(evt[1], JobEvent) and evt[1].event == JobEvent.TERMINATED:
                task_first_exec[task].append(
                    (job_count, evt[1].job.activation_date, executed_time / cycles_per_ms, evt[0] / cycles_per_ms))
                job_count += 1

                # Continue with the next task if more than njobs jobs were processed
                if len(task_first_exec[task]) >= njobs:
                    break  # for

            if isinstance(evt[1], SlackEvent) and evt[1].event == SlackEvent.CALC_SLACK:
                task_slack_cc[task].append((evt[0] / cycles_per_ms, evt[1].slack, evt[1].slack_results))

    return task_first_exec, task_slack_cc


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("file", help="XML file with task-sets", type=str)
    return parser.parse_args()


def main():
    root = Tk()
    gui = MainGui(root)
    root.mainloop()
"""
    # Verify that the task-set is schedulable
    schedulable = rta3(rts, True)

    if schedulable:
        try:
            slack_methods = [SlackFixed()]
            cfg = create_configuration(rts, slack_methods, 6)
            model = create_model(cfg, slack_methods)
            model.run_model()

            for log in model.logs:
                print(log)

            for task in model.results.tasks:
                print(task.name + ":")
                for job in task.jobs:
                    print("{} {:.3f} ms".format(job.name, job.computation_time))

            for task in model.results.tasks.values():
                print("{} {}".format(task.name, task.preemption_count))
        except NegativeSlackException as exc:
            print(exc)
            """


if __name__ == '__main__':
    main()
