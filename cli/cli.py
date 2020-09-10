from simulations.slack.simslack import run_sim, print_results, process_results
from concurrent.futures import ProcessPoolExecutor
from tqdm.auto import tqdm
from resources.xml import load_from_file
from tabulate import tabulate


def mixrange(s):
    """
    Create a list of numbers from a string. Ie: "1-3,6,8-10" into [1,2,3,6,8,9,10]
    :param s: a string
    :return: a list of numbers
    """
    r = []
    for i in s.split(','):
        if '-' not in i:
            r.append(int(i))
        else:
            l, h = map(int, i.split('-'))
            r += range(l, h+1)
    return r


def run_simulation(args):
    if args.instance_count <= 0:
        print("Instance count", "Instance count must be greater than 0.")
        return

    rts_list = mixrange(args.rts)
    if len(rts_list) == 1:
        run_single_simulation(load_from_file(args.file, rts_list)[0], args)
    else:
        run_multiple_simulation(rts_list, args)


def print_tasks(tasks):
    """
    Print the task set into stdout without the ss field. This should use some form of filter instead of deepcopy.
    :param tasks: rts
    :return: None
    """
    import copy
    tasks_copy = copy.deepcopy(tasks)
    for task in tasks_copy:
        del task["ss"]  # dirty as hell
    print("Tasks:")
    print(tabulate(tasks_copy, tablefmt="github", headers="keys"))


def run_single_simulation(rts, args):
    """
    Simulate an rts
    :param rts: task set
    :param args: parameters
    :return: None
    """

    print("File: {0}".format(args.file.name))
    print("RTS: {0}".format(rts["id"]))
    print("FU: {:.2%}".format(rts["fu"]))
    print("LCM: {:.5E}".format(rts["lcm"]))
    print("Instances: {0}".format(args.instance_count))
    print_tasks(rts["tasks"])

    params = {
        "instance_cnt": args.instance_count,
        "slack_classes": args.ss_methods,
    }

    with tqdm(total=100, ascii=True, desc="Simulating...") as progress:
        sim_result = run_sim(rts, params, progress.update)
        progress.update(progress.total - progress.n)

    if sim_result["error"]:
        print("Simulation failed!")
        print("\t{0}".format(sim_result["error_msg"]))
    else:
        print("Simulation successful!")
        print("SS CC:")
        if args.instance_count < 20:
            for ss_method, ss_result in sim_result['cc'].items():
                table_tasks = ["T{:d}".format(n + 1) for n in range(len(ss_result))]
                print("{0}".format(ss_method))
                print(tabulate(ss_result, showindex=table_tasks, headers=range(1, args.instance_count + 1),
                               tablefmt="github"))

        results, error_cnt, not_schedulable_cnt, error_list = process_results([sim_result], "mean_std")
        print_results(results)

        if args.gantt_gui:
            from gui.gantt import create_gantt_window
            from PyQt5.QtWidgets import QApplication
            import sys
            app = QApplication(sys.argv)
            ex = create_gantt_window(sim_result["model"])
            return app.exec_()

        if args.gantt:
            from gui.gantt import GanttCanvas
            from PyQt5.QtCore import QCoreApplication
            import sys
            elements = []
            elements.extend(sim_result["model"].processors)
            elements.extend(sim_result["model"].task_list)
            app = QCoreApplication(sys.argv)
            canvas = GanttCanvas(sim_result["model"], (0, sim_result["model"].duration // sim_result["model"].cycles_per_ms,  elements))
            canvas.saveImgToFile("simulation.png")
            return app.exec_()


def run_multiple_simulation(rts_ids_list: list, args):
    """
    Run multiple simulations in parallelel.
    :param rts_ids_list:
    :param args:
    :return:
    """
    print("File: {0}".format(args.file.name))
    print("# of RTS to simulate: {0}".format(len(rts_ids_list)))
    print("# of instances per task: {0}".format(args.instance_count))

    params = {"instance_cnt": args.instance_count, "slack_classes": args.ss_methods}

    results = []

    with tqdm(total=len(rts_ids_list), ascii=True, desc="Simulating...") as progress:
        with ProcessPoolExecutor() as executor:
            def future_process_result(f):
                progress.update()
                results.append(f.result())

            for rts in load_from_file(args.file, rts_ids_list):
                future = executor.submit(run_sim, rts, params, None)
                future.add_done_callback(future_process_result)

    results, error_cnt, not_schedulable_cnt, error_list = process_results(results, "mean_std")
    print_results(results)

