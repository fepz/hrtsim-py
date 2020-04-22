from simso.configuration import Configuration
from simso.core import Model

from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import add_slack_data


def create_configuration(rts, slack_methods, instance_count):
    # Create a SimSo configuration object.
    configuration = Configuration()

    # Simulate until the lower priority task has n instantiations.
    configuration.duration = (rts[-1]["T"] * (instance_count + 1)) * configuration.cycles_per_ms

    # Add the required fields for slack stealing simulation.
    add_slack_data(rts, slack_methods)

    # Create the tasks and add them to the SimSo configuration.
    for task in rts:
        configuration.add_task(name="T_{0}".format(int(task["nro"])), identifier=int(task["nro"]),
                               period=task["T"], activation_date=0, deadline=task["D"], wcet=task["C"],
                               data=task["slack_data"])

    # Add a processor.
    configuration.add_processor(name="CPU 1", identifier=1)

    # Add a scheduler.
    configuration.scheduler_info.filename = "schedulers/slack/RM_mono_slack.py"
    # configuration.scheduler_info.clas = "simso.schedulers.RM"

    # Check the config before trying to run it.
    configuration.check_all()

    return configuration


def create_model(configuration, slack_methods, instance_count):
    # Creates a SimSo model from the provided SimSo configuration.
    model = Model(configuration)

    # Add the slack methods to evaluate.
    model.scheduler.data["slack_methods"] = slack_methods

    # Number of instances to record.
    model.scheduler.data["instance_count"] = instance_count

    # Calculate task's slack at zero.
    for task in model.task_list:
        task.data["slack"], task.data["ttma"], _, _ = slack_methods[0].get_slack(task, model.task_list, 0)
        task.data["k"] = task.data["slack"]
        if task.data["slack"] < 0:
            raise NegativeSlackException(0, task, slack_methods[0].method_name)

    return model


def run_simulation(model):
    model.run_model()
