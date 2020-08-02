import numpy as np
from tabulate import tabulate
from collections import defaultdict
from simso.configuration import Configuration
from simso.core import Model
from rta.rta3 import rta3
from resources.xml import load_from_xml
from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import add_slack_data, get_slack_methods


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


def create_model(configuration, slack_methods, instance_count, callback=None):
    # Creates a SimSo model from the provided SimSo configuration.
    model = Model(configuration, callback)

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


def run_sim(rts_id, params, callback=None):
    def private_callback(clock):
        if callback:
            callback(rts_id, clock)

    # Load the rts from file.
    rts = load_from_xml(params["file"], rts_id)

    results = dict()
    results["rts_id"] = rts_id
    results["error"] = False
    results["cc"] = dict()

    try:
        # Verify that the task-set is schedulable.
        results["schedulable"] = rta3(rts, True)
        if results["schedulable"]:
            # Instantiate slack methods.
            slack_methods = []
            for ss_method in params["slack_classes"]:
                slack_class = get_slack_methods()[ss_method]
                slack_methods.append(get_class(slack_class)())

            # Create SimSo configuration and model.
            cfg = create_configuration(rts, slack_methods, params["instance_cnt"])
            model = create_model(cfg, slack_methods, params["instance_cnt"], private_callback)

            if callback is not None:
                callback(rts_id, 0, cfg.duration)

            # Run the simulation.
            model.run_model()

            if callback is not None:
                callback(rts_id, cfg.duration, None, True)

            # For each slack method's creates an Numpy matrix [ tasks x instances ]
            for slack_method in slack_methods:
                slack_method_results = []
                for task in model.task_list:
                    slack_method_results.append(task.data[slack_method.method_name]["cc"])
                results["cc"][slack_method.method_name] = np.array(slack_method_results)

    except NegativeSlackException as exc:
        results["error"] = True
        results["error_msg"] = str(exc)

    except KeyError as exc:
        results["error"] = True
        results["error_msg"] = "Slack Method not found: {0}.".format(str(exc))

    return results


def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


def print_results_options():
    return ["table", "csv"]


def result_process_options():
    return list(process_types.keys())


def process_results_mean_only(r):
    tasks_means = []
    for method_name, method_cc in r.items():
        # Genera arreglo (tareas x instancias) con la media de todos los sistemas simulados.
        r_mean = np.mean(method_cc, axis=2, dtype=np.float32)
        # Genera un vector con la media de las instancias por tarea.
        tasks_means.append(np.mean(r_mean, axis=0, dtype=np.float32))

    return tasks_means


def process_results_mean_std():
    return


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


def process_result(rts_result):
    process_result.queue.put(rts_result["rts_id"])
    if not rts_result["error"]:
        if rts_result["schedulable"]:
            aggregate_results["schedulable_count"] += 1
        else:
            aggregate_results["non_schedulable_list"].append(rts_result["rts_id"])
    else:
        aggregate_results["error_list"].append("RTS {:d}: {:s}.\n".format(rts_result["rts_id"], rts_result["error_msg"]))


def get_aggregate_results():
    return aggregate_results


def reset_aggregate_results():
    aggregate_results["schedulable_count"] = 0
    aggregate_results["non_schedulable_list"] = []
    aggregate_results["error_count"] = 0
    aggregate_results["error_list"] = []


def process_results(results, process_type):
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

    return process_types[process_type](r), error_cnt, not_schedulable_cnt, error_list


def print_results(results, print_as="table"):
    r = defaultdict(list)

    not_schedulable_cnt = 0
    error_cnt = 0

    result_list = []
    error_list = []

    for result in results:
        if not result["error"]:
            if result["schedulable"]:
                for method_name, method_cc in result["cc"].items():
                    r[method_name].append(method_cc)
            else:
                not_schedulable_cnt += 1
                error_list.append("RTS {:d}: not schedulable.\n".format(result["rts_id"]))
        else:
            error_cnt += 1
            error_list.append("RTS {:d}: {:s}.\n".format(result["rts_id"], result["error_msg"]))

    tasks_means = []
    for method_name, method_cc in r.items():
        # Genera arreglo (tareas x instancias) con la media de todos los sistemas simulados.
        r_mean = np.mean(method_cc, axis=2, dtype=np.float32)
        # Genera un vector con la media de las instancias por tarea.
        tasks_means.append(np.mean(r_mean, axis=0, dtype=np.float32))

    if print_as == "table":
        table_methods = list(r.keys())
        table_tasks = ["T{:d}".format(n + 1) for n in range(len(tasks_means[0]))]
        result_list.append("{}\n".format(tabulate(np.array(tasks_means).transpose(), showindex=table_tasks,
                                                  headers=table_methods, floatfmt=".4f", tablefmt="github")))
    elif print_as == "csv":
        from io import StringIO
        s = StringIO()
        np.savetxt(s, np.array(tasks_means).transpose(), fmt="%.4f")
        result_list.append("{}\n".format(s.getvalue()))

    return result_list, error_list, error_cnt, not_schedulable_cnt


