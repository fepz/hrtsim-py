from simso.configuration import Configuration
from simso.core import Model
from slack.SlackExceptions import NegativeSlackException, DifferentSlackException


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
    def __init__(self):
        return

    def observe(self, y,t = None):
        return

    def __len__(self):
        return 0


def create_configuration(rts, slack_methods, instance_count, scheduler):
    """

    :param rts:
    :param slack_methods:
    :param instance_count:
    :return:
    """
    # Create a SimSo configuration object.
    configuration = Configuration()

    # Simulate until the lower priority periodic task has n instantiations.
    configuration.duration = (rts["ptasks"][-1]["T"] * (instance_count + 1)) * configuration.cycles_per_ms

    # Add some extra required fields for slack stealing simulation.
    for ptask in rts["ptasks"]:
        # Each slack method needs its own copy of A, B, C and CC (computational cost).
        for ss_method in slack_methods:
            ptask["ss"][ss_method] = {'a': ptask["C"], 'b': ptask["T"], 'c': 0}

    # Create the periodic tasks and add them to the SimSo configuration.
    for ptask in rts["ptasks"]:
        configuration.add_task(name="T_{0}".format(int(ptask["nro"])), identifier=int(ptask["nro"]),
                               period=ptask["T"], activation_date=0, deadline=ptask["D"], wcet=ptask["C"],
                               data=ptask)

    # Create the aperiodic tasks and add them to the SimSo configuration.
    for atask in rts["atasks"]:
        configuration.add_task(name="A_{0}".format(int(atask["nro"])), identifier=int(10+atask["nro"]),
                               deadline=1000, wcet=atask["C"], task_type="Sporadic", data=atask, 
                               list_activation_dates=[atask["a"]])

    # Add a processor.
    configuration.add_processor(name="CPU 1", identifier=1)

    # Add a scheduler.
    configuration.scheduler_info.clas = scheduler

    # Check the config before trying to run it.
    configuration.check_all()

    return configuration


def run_sim(params: dict) -> dict:
    """
    Run the simulation of a rts.
    :param rts: rts to simulate.
    :param params: simulation parameters.
    :param callback: callback to be called from simso.
    :return: a dict with the simulation results
    """
    result = {
        "error": False,
    }

    try:
        # Create SimSo configuration and model.
        cfg = create_configuration(params["rts"], params["ss_methods"], params["instance_count"], params["scheduler"])

        # Creates a SimSo model from the provided SimSo configuration.
        model = Model(cfg)
        # Add the slack methods to evaluate.
        model.scheduler.data["ss_methods"] = params["ss_methods"]
        # Number of instances to record.
        model.scheduler.data["instance_count"] = params["instance_count"]

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

    finally:
        if params["gantt"]:
            result["model"] = model

    return result

