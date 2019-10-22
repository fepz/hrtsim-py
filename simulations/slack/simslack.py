from simso.configuration import Configuration
from simso.core import Model

from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import add_slack_data


def create_configuration(rts, slack_methods, njobs):
    configuration = Configuration()

    # Simulate until the lower priority task has ntask instantiations
    configuration.duration = (rts[-1]["T"] * (njobs + 1)) * configuration.cycles_per_ms

    # add slack data to tasks
    add_slack_data(rts, slack_methods)

    # create tasks
    for task in rts:
        # add the periodic task to the model
        configuration.add_task(name="T_{0}".format(int(task["nro"])), identifier=int(task["nro"]),
                               period=task["T"], activation_date=0, deadline=task["D"], wcet=task["C"],
                               data=task["slack_data"])

    # Add a processor:
    configuration.add_processor(name="CPU 1", identifier=1)

    # Add a scheduler:
    configuration.scheduler_info.filename = "schedulers/slack/RM_mono_slack.py"
    # configuration.scheduler_info.clas = "simso.schedulers.RM"

    # Check the config before trying to run it.
    configuration.check_all()

    return configuration


def create_model(configuration, slack_methods):
    # Init a model from the configuration.
    model = Model(configuration)

    # Add the slack method to the scheduler
    model.scheduler.data["slack_methods"] = slack_methods

    # Calculate slack at zero
    for task in model.task_list:
        task.data["slack"], task.data["ttma"], _, _ = slack_methods[0].get_slack(task, model.task_list, 0)
        task.data["k"] = task.data["slack"]
        if task.data["slack"] < 0:
            raise NegativeSlackException(0, task, slack_methods[0].method_name)

    # reset ss counters
    for task in model.task_list:
        task.data[slack_methods[0].method_name] = {'a': task.wcet, 'b': task.period, 'c': 0}

    return model


def run_simulation(model):
    model.run_model()
