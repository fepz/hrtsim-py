from simulations.slack.simslack import run_sim, print_results, process_result, get_aggregate_results
from rich.progress import Progress, TextColumn, BarColumn, DownloadColumn, TimeRemainingColumn
from rich import print
from multiprocessing import Pool, Queue, SimpleQueue
from concurrent.futures import ProcessPoolExecutor
import threading
import queue
import multiprocessing.dummy
import simulations.slack.simslack as slacksim
import itertools


def run_sim_async(rts_id, params, progress_task):
    def progress_update(clock, total=None):
        if total is not None:
            progress.update(progress_task, total=total)
        progress.update(progress_task, completed=clock)

    return run_sim(rts_id, params, progress_update)


def mixrange(s):
    r = []
    for i in s.split(','):
        if '-' not in i:
            r.append(int(i))
        else:
            l, h = map(int, i.split('-'))
            r += range(l, h+1)
    return r


def test(r):
    print(r)


"""
progress = Progress(
    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
    BarColumn(bar_width=None),
    "[progress.percentage]{task.percentage:>3.1f}%",
    "•",
    TimeRemainingColumn(),
)
"""


def future_process_result(f):
    process_result(f.result())


def progress_callback(rts_id, completed, total=None, finished=False):
    progress_callback.queue.put([rts_id, completed, total, finished])


class MultipleSimulationCli:

    def __init__(self, args):
        self.file = args.file
        self.rts_list = mixrange(args.rts)
        self.instance_count = args.instance_count
        self.ss_methods = args.ss_methods
        self.simulation_results = None
        print("File: {0}".format(self.file))
        print("Instance count: {0}".format(self.instance_count))

        self.progress = Progress()
        self.progress_dict = {}

        # Initialize Queue.
        self.results_queue = SimpleQueue()
        self.progress_queue = SimpleQueue()

    def run_simulation(self):
        process_result.queue = self.results_queue
        progress_callback.queue = self.progress_queue
        slacksim.reset_aggregate_results()

        params = {"file": self.file, "instance_cnt": self.instance_count, "slack_classes": self.ss_methods}

        with ProcessPoolExecutor() as executor:
            for rts_id in self.rts_list:
                future = executor.submit(run_sim, rts_id, params, progress_callback)
                future.add_done_callback(future_process_result)

            with self.progress:
                rts_count = len(self.rts_list)
                while rts_count > 0:
                    while not self.progress.finished:
                        try:
                            args = self.progress_queue.get()  # Could use non-blocking mode.
                            rts_id = args[0]
                            if args[2]:
                                self.progress_dict[rts_id] = self.progress.add_task("[green]RTS {0}... ".format(rts_id), total=args[2])
                            else:
                                self.progress.update(self.progress_dict[rts_id], completed=args[1])
                            if args[3]:
                                rts_count = rts_count - 1
                        except queue.Empty:  # Only when using non-blocking mode.
                            pass
                        except OSError:  # For Python version > 3.8 should be ValueError.
                            pass
                        except EOFError:  # The queue was closed.
                            pass

        agg_results = get_aggregate_results()
        print(agg_results)

    def run_simulation_thread2(self, result_queue, progress_queue):
        process_result.queue = result_queue
        progress_callback.queue = progress_queue
        slacksim.reset_aggregate_results()

        params = {"file": self.file, "instance_cnt": self.instance_count, "slack_classes": self.ss_methods}

        with self.progress:
            with ProcessPoolExecutor() as executor:
                for rts_id in self.rts_list:
                    self.progress_dict[rts_id] = self.progress.add_task("Simulating RTS {0}... ".format(rts_id))
                    future = executor.submit(run_sim, rts_id, params, progress_callback)
                    future.add_done_callback(future_process_result)

        agg_results = get_aggregate_results()
        print(agg_results)

    def run_simulation_thread(self):
        process_result.queue = self.results_queue
        progress_callback.queue = self.progress_queue
        slacksim.reset_aggregate_results()

        params = {"file": self.file, "instance_cnt": self.instance_count, "slack_classes": self.ss_methods}

        with Pool() as pool:
            iter = zip(self.rts_list, itertools.repeat(params), itertools.repeat(progress_callback))
            pool.starmap_async(run_sim, iter, callback=process_result, error_callback=test)

    def wait_simulation_thread(self):
        #while self.sim_thread.is_alive():
        rts_count = len(self.rts_list)
        with Progress() as progress:
            while rts_count > 0:
                try:
                    args = self.progress_queue.get()  # Could use non-blocking mode.
                    rts_id = args[0]
                    if args[2]:
                        self.progress_dict[rts_id] = progress.add_task("Simulating RTS {0}... ".format(rts_id), total=args[2])
                    else:
                        progress.update(self.progress_dict[rts_id], completed=args[1])
                    if args[3]:
                        rts_count = rts_count - 1;
                except queue.Empty:  # Only when using non-blocking mode.
                    pass
                except OSError:  # For Python version > 3.8 should be ValueError.
                    pass
                except EOFError:  # The queue was closed.
                    pass

    def run_simulation2(self):

        process_result.queue = self.queue
        slacksim.reset_aggregate_results()

        with Progress() as progress:
            with Pool() as pool:
                def run_sim2(rts_id):
                    def progress_update(task, clock, total=None):
                        if total is not None:
                            progress.update(task, total=total)
                        progress.update(task, completed=clock)

                    progress_task = progress.add_task("Simulating RTS {0}... ".format(rts_id)) #, filename="RTS {0}".format(rts_id))
                    params = {"file": self.file, "instance_cnt": self.instance_count, "rts_count": 0,
                              "slack_classes": self.ss_methods, "progress_task": progress_task}
                    run_sim(rts_id, params, progress_update)

                #pool.map_async(run_sim2, self.rts_list, callback=process_result, error_callback=test)
                params = {"file": self.file, "instance_cnt": self.instance_count, "rts_count": 0,
                          "slack_classes": self.ss_methods}
                pool.map_async(run_sim, self.rts_list, callback=process_result, error_callback=test)
                pool.close()
                pool.join()

        agg_results = get_aggregate_results()
        print(agg_results)


    def run_simulation3(self):

        process_result.queue = self.queue
        slacksim.reset_aggregate_results()

        with Progress() as progress:
            with Pool() as pool:
                def progress_update(task, clock, total=None):
                    if total is not None:
                        progress.update(task, total=total)
                    progress.update(task, completed=clock)

                for rts_id in self.rts_list:
                    progress_task = progress.add_task("Simulating RTS {0}... ".format(rts_id)) #, filename="RTS {0}".format(rts_id))
                    #progress_update = lambda clock, total: progress.update(progress_task, total=total) if total else progress.update(progress_task, completed=clock)
                    params = {"file": self.file, "instance_cnt": self.instance_count, "rts_count": 0,
                              "slack_classes": self.ss_methods, "progress_task": progress_task}
                    pool.apply_async(run_sim, (rts_id, params, ), callback=process_result, error_callback=test)
                    #pool.apply_async(run_sim_async, (rts_id, params, progress, progress_task), callback=process_result, error_callback=test)
                pool.close()
                pool.join()

        agg_results = get_aggregate_results()
        print(agg_results)

