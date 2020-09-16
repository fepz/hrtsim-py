import numpy as np
from tabulate import tabulate
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
            task["ss"][ss_method] = {'a': task["C"], 'b': task["T"], 'c': 0, 'cc': []}

    # Create the tasks and add them to the SimSo configuration.
    for task in rts["tasks"]:
        configuration.add_task(name="T_{0}".format(int(task["nro"])), identifier=int(task["nro"]),
                               period=task["T"], activation_date=0, deadline=task["D"], wcet=task["C"],
                               data=task)

    # Add a processor.
    configuration.add_processor(name="CPU 1", identifier=1)

    # Add a scheduler.
    configuration.scheduler_info.filename = "schedulers/slack/RM_mono_slack.py"
    #configuration.scheduler_info.clas = "simso.schedulers.RM"

    # Check the config before trying to run it.
    configuration.check_all()

    return configuration


def run_sim(rts: dict, params: dict, callback=None, sink=True, retrieve_model=False) -> dict:
    """

    :param rts:
    :param params:
    :param callback:
    :return:
    """
    result = {
        "rts_id": rts["id"],
        "schedulable": rts["schedulable"],
        "error": False,
        "cc": {}
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

            # Discard trace information to reduce memory footprint
            if sink:
                model._logger = SinkLogger(model)
                for task in model.scheduler.task_list:
                    task._monitor = SinkMonitor()
                for cpu in model.scheduler.processors:
                    cpu.monitor = SinkMonitor()

            # Run the simulation.
            model.run_model()

            # For each slack method's creates an Numpy matrix [ tasks x instances ]
            for ss_method in params["ss_methods"]:
                result["cc"][ss_method] = np.array([task.data["ss"][ss_method]["cc"] for task in model.task_list])

            # Add model
            if retrieve_model:
                result["model"] = model
        else:
            result["error"] = True
            result["error_msg"] = "No schedulable."

    except (NegativeSlackException, DifferentSlackException) as exc:
        result["error"] = True
        result["error_msg"] = str(exc)

    except KeyError as exc:
        result["error"] = True
        result["error_msg"] = "Slack Method not found: {0}.".format(str(exc))

    return result


def print_summary_of_results(results):
    error_count = 0
    error_list = []
    schedulable_count = 0
    not_schedulable_count = 0
    for result in results:
        if not result["error"]:
            if result["schedulable"]:
                schedulable_count += 1
            else:
                not_schedulable_count += 1
        else:
            error_count += 1
            error_list.append("RTS {:d}: {:s}.\n".format(result["rts_id"], result["error_msg"]))
    print("# of errors: {0:}".format(error_count))
    if error_count > 0:
        for error_msg in error_list:
            print("\t{0:}".format(error_msg))
    print("# of schedulable systems: {0:}".format(schedulable_count))
    print("# of not schedulable systems: {0:}".format(not_schedulable_count))


def print_means(results):
    r = defaultdict(list)
    for result in results:
        if not result["error"]:
            if result["schedulable"]:
                for method_name, method_cc in result["cc"].items():
                    r[method_name].append(method_cc)

    tasks_means = dict()
    for method_name, method_cc in r.items():
        # Genera arreglo (tareas x instancias) con la media de todos los sistemas simulados.
        r_mean = np.mean(method_cc, axis=2, dtype=np.float32)
        # Genera un vector con la media de las instancias por tarea.
        tasks_means[method_name] = np.mean(r_mean, axis=0, dtype=np.float32)

    print_results(tasks_means)


def print_results(results, print_as="table", stdout=True):
    """
    Prints results of the simulation.
    :param results: results
    :param print_as: table or csv
    :return: nothing
    """
    # Se obtiene el número de tareas contando el número de resultados del primer método
    row_index = ["T{:d}".format(n + 1) for n in range(len(results[list(results.keys())[0]]))]
    if print_as == "table":
        table = tabulate(results, headers="keys", floatfmt=".4f", tablefmt="github", showindex=row_index)
        if stdout:
            print(table)
        else:
            return table
