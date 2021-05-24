from collections import defaultdict
from simso.configuration import Configuration
from simso.core import Model
from slack.SlackExceptions import NegativeSlackException, DifferentSlackException


class SinkLogger(object):
    """
    Simple logger. Every message is logged with its date.
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


def create_configuration(rts, slack_methods, instance_count):
    """

    :param rts:
    :param slack_methods:
    :param instance_count:
    :return:
    """
    # Create a SimSo configuration object.
    configuration = Configuration()

    # Simulate until the lower priority task has n instantiations.
    configuration.duration = (rts["tasks"][-1]["T"] * (instance_count + 1)) * configuration.cycles_per_ms

    # Add some extra required fields for slack stealing simulation.
    for task in rts["tasks"]:
        # Each slack method needs its own copy of A, B, C and CC (computational cost).
        for ss_method in slack_methods:
            task["ss"][ss_method] = {'a': task["C"], 'b': task["T"], 'c': 0}

    # Create the tasks and add them to the SimSo configuration.
    for task in rts["tasks"]:
        configuration.add_task(name="T_{0}".format(int(task["nro"])), identifier=int(task["nro"]),
                               period=task["T"], activation_date=0, deadline=task["D"], wcet=task["C"],
                               data=task)

    # Add a processor.
    configuration.add_processor(name="CPU 1", identifier=1)

    # Add a scheduler.
    configuration.scheduler_info.filename = "schedulers/RM_mono_slack.py"
    #configuration.scheduler_info.clas = "simso.schedulers.RM"

    # Check the config before trying to run it.
    configuration.check_all()

    return configuration


def run_sim(rts: dict, params: dict, callback=None, sink=True, retrieve_model=False) -> dict:
    """
    Run the simulation of a rts.
    :param rts: rts to simulate.
    :param params: simulation parameters.
    :param callback: callback to be called from simso.
    :return: a dict with the simulation results
    """
    result = {
        "rts_id": rts["id"],
        "schedulable": rts["schedulable"],
        "error": False,
    }

    try:
        if rts["schedulable"]:
            # Callback
            def private_callback(clock):
                if callback:
                    progress = int((clock / cfg.duration) * 10)
                    callback(progress)

            # Create SimSo configuration and model.
            cfg = create_configuration(rts, params["ss_methods"], params["instance_cnt"])

            # Creates a SimSo model from the provided SimSo configuration.
            model = Model(cfg, private_callback if callback else None)
            # Add the slack methods to evaluate.
            model.scheduler.data["slack_methods"] = params["ss_methods"]
            # Number of instances to record.
            model.scheduler.data["instance_count"] = params["instance_cnt"]

            model.scheduler.data["results"] = {}
            model.scheduler.data["results"]["ss-cc"] = {}
            for ss_method in params["ss_methods"]:
                model.scheduler.data["results"]["ss-cc"][(ss_method, "cc")] = {}
            model.scheduler.data["results"]["ss-theo"] = defaultdict(lambda: defaultdict(int))

            # Discard trace information to reduce memory footprint
            if sink:
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
        result["error_msg"] = "Slack Method not found: {0}.".format(str(exc))

    return result

