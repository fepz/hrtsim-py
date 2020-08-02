from resources.xml import load_from_xml
from rta.rta3 import rta3
from simulations.slack.simslack import run_sim, print_results
from slack.SlackExceptions import NegativeSlackException
from tabulate import tabulate
from rich.progress import Progress


class SingleSimulationCli:

    def __init__(self, args):
        self.rts_id = args.rts
        self.file = args.file
        self.instance_count = args.instance_count
        self.ss_methods = args.ss_methods
        self.rts = load_from_xml(self.file, int(self.rts_id))
        self.schedulable = rta3(self.rts, True)
        print("File: {0}".format(self.file))
        print("RTS id: {0}".format(self.rts_id))
        print("Instance count: {0}".format(self.instance_count))
        print("Schedulable: {0}".format(self.schedulable))
        print("RTS tasks:")
        print(tabulate(self.rts, tablefmt="github", headers="keys"))

    def run_simulation(self):

        # Get the number of instances to evaluate.
        if self.instance_count <= 0:
            print("Instance count", "Instance count must be greater than 0.")
            return

        try:
            params = {
                "instance_cnt": self.instance_count,
                "slack_classes": self.ss_methods,
                "file": self.file
            }

            print("Running simulation...")

            with Progress() as progress:
                progress_task = progress.add_task("Simulating... ")

                def progress_update(clock, total=None):
                    if total is not None:
                        progress.update(progress_task, total=total)
                    progress.update(progress_task, completed=clock)

                sim_result = run_sim(self.rts_id, params, progress_update)

            if sim_result["error"]:
                print("Simulation failed!")
                print("\t{0}".format(sim_result["error_msg"]))
            if not sim_result["error"]:
                print("Simulation successful!")
                print("SS CC:")
                if self.instance_count < 20:
                    for ss_method, ss_result in sim_result['cc'].items():
                        table_tasks = ["T{:d}".format(n + 1) for n in range(len(ss_result))]
                        print("{0}".format(ss_method))
                        print(tabulate(ss_result, showindex=table_tasks, headers=range(1, self.instance_count + 1),
                                       tablefmt="github"))

                print("Means per task:")
                results_list, error_list, not_schedulable_cnt, error_cnt = print_results([sim_result])
                for r in results_list:
                    print(r)

        except NegativeSlackException as exc:
            print(exc)

