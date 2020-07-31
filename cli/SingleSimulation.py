from resources.xml import load_from_xml
from rta.rta3 import rta3
from simulations.slack.simslack import run_sim, print_results
from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import get_slack_methods
from tabulate import tabulate
from rich.progress import Progress


def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


class SingleSimulationCli:

    def __init__(self, args):
        self.rts_id = args.rts
        self.file = args.file
        self.instance_count = args.instance_count
        self.ss_method = args.ss_method
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
                "slack_classes": [],
                "file": self.file
            }
            for ss_method in self.ss_method:
                params["slack_classes"].append((ss_method, get_slack_methods()[ss_method]))

            print("Running simulation...")

            with Progress() as progress:
                progress_task = progress.add_task("Simulating... ")

                def progress_update(clock, total=None):
                    if total is not None:
                        progress.update(progress_task, total=total)
                    progress.update(progress_task, completed=clock)

                sim_result = run_sim(self.rts_id, params, progress_update)

            print("Simulation results:")
            print("Errors: {0}".format(sim_result["error"]))
            print("SS CC:")
            if self.instance_count < 20:
                print(tabulate(sim_result['cc']["Fixed2"], showindex=range(1, len(sim_result['cc']['Fixed2'])+1),
                               headers=range(1, self.instance_count+1), tablefmt="github"))

            print("Means per task:")
            results_list, error_list, not_schedulable_cnt, error_cnt = print_results([sim_result])
            for r in results_list:
                print(r)

        except NegativeSlackException as exc:
            print(exc)

