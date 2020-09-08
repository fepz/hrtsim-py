import numpy as np
from tabulate import tabulate
from collections import defaultdict
from simso.configuration import Configuration
from simso.core import Model
from slack.SlackExceptions import NegativeSlackException, DifferentSlackException


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


def run_sim(rts, params, callback=None):
    """

    :param rts:
    :param params:
    :param callback:
    :return:
    """
    results = dict()
    results["rts_id"] = rts["id"]
    results["schedulable"] = rts["schedulable"]
    results["error"] = False
    results["cc"] = dict()

    try:
        if rts["schedulable"]:
            # Callback
            def private_callback(clock):
                if callback:
                    progress = int((clock / cfg.duration) * 10)
                    callback(progress)

            # Create SimSo configuration and model.
            cfg = create_configuration(rts, params["slack_classes"], params["instance_cnt"])

            # Creates a SimSo model from the provided SimSo configuration.
            model = Model(cfg, private_callback)
            # Add the slack methods to evaluate.
            model.scheduler.data["slack_methods"] = params["slack_classes"]
            # Number of instances to record.
            model.scheduler.data["instance_count"] = params["instance_cnt"]

            # Run the simulation.
            model.run_model()

            # For each slack method's creates an Numpy matrix [ tasks x instances ]
            for slack_method in params["slack_classes"]:
                slack_method_results = []
                for task in model.task_list:
                    slack_method_results.append(task.data["ss"][slack_method]["cc"])
                results["cc"][slack_method] = np.array(slack_method_results)

            # Add model
            results["model"] = model

    except (NegativeSlackException, DifferentSlackException) as exc:
        results["error"] = True
        results["error_msg"] = str(exc)

    except KeyError as exc:
        results["error"] = True
        results["error_msg"] = "Slack Method not found: {0}.".format(str(exc))

    return results


def print_results_options():
    return ["table", "csv"]


def process_results_mean_only(r):
    """

    :param r:
    :return:
    """
    tasks_means = dict()
    for method_name, method_cc in r.items():
        # Genera arreglo (tareas x instancias) con la media de todos los sistemas simulados.
        r_mean = np.mean(method_cc, axis=2, dtype=np.float32)
        # Genera un vector con la media de las instancias por tarea.
        tasks_means[method_name] = np.mean(r_mean, axis=0, dtype=np.float32)

    return tasks_means


def process_results_mean_std(r):
    """

    :param r:
    :return:
    """
    tasks_means = dict()
    for method_name, method_cc in r.items():
        # Genera arreglo (tareas x instancias) con la media de todos los sistemas simulados.
        r_mean = np.mean(method_cc, axis=2, dtype=np.float32)
        r_std = np.std(method_cc, axis=2, dtype=np.float32)
        # Genera un vector con la media de las instancias por tarea.
        tasks_means["{0}_mean".format(method_name)] = np.mean(r_mean, axis=0, dtype=np.float32)
        tasks_means["{0}_std".format(method_name)] = np.std(r_mean, axis=0, dtype=np.float32)

    return tasks_means


def result_process_options():
    return list(process_types.keys())


process_types = {
    "mean_only": process_results_mean_only,
    "mean_std": process_results_mean_std
}

aggregate_results = {
    "schedulable_count": 0,
    "non_schedulable_list": [],
    "error_count": 0,
    "error_list": []
}


def process_results(results, process_type):
    """
    Process simulation results.
    :param results: simulation results
    :param process_type: kind of analysis to perform to the results
    :return: analysis result, non-schedulable count, error count and error list
    """
    r = defaultdict(list)

    schedulable_cnt = 0
    not_schedulable_cnt = 0
    error_cnt = 0

    error_list = []

    for result in results:
        if not result["error"]:
            if result["schedulable"]:
                schedulable_cnt += 1
                for method_name, method_cc in result["cc"].items():
                    r[method_name].append(method_cc)
            else:
                not_schedulable_cnt += 1
                error_list.append("RTS {:d}: not schedulable.\n".format(result["rts_id"]))
        else:
            error_cnt += 1
            error_list.append("RTS {:d}: {:s}.\n".format(result["rts_id"], result["error_msg"]))

    return process_types[process_type](r), not_schedulable_cnt, error_cnt, error_list


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
