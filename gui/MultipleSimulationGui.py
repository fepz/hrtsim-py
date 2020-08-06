import os
import queue

import multiprocessing.dummy
from multiprocessing import Pool, Queue, Lock
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Progressbar
from argparse import ArgumentParser

from schedulers.SchedulerUtil import get_schedulers
from slack.SlackUtils import get_slack_methods
from simulations.slack.simslack import run_sim, print_results, print_results_options, process_results
from concurrent.futures import ProcessPoolExecutor
from resources.xml import load_from_xml


def future_process_result(f):
    future_process_result.queue.put(f.result())


def run_simulation_thread(rqueue, params):
    future_process_result.queue = rqueue
    with ProcessPoolExecutor() as executor:
        for rts_id in range(1, params["rts_count"] + 1):
            future = executor.submit(run_sim, load_from_xml(params["file"], rts_id), params, None)
            future.add_done_callback(future_process_result)


class MultipleSimulationGui(Toplevel):

    def __init__(self):
        Toplevel.__init__(self)
        self.title("Multiple Simulation")

        # Queue.
        self.queue = None

        # Thread to run the simulations.
        self.sim_thread = None
        self.wait_thread = None

        # Simulation results
        self.results = []

        # List of widgets that can be enabled/disabled.
        self.widgetList = []

        self.selectedFile = None
        self.openFile = Button(self, text="Open XML file", command=self.open_file)
        self.widgetList.append(self.openFile)
        self.selectedFileLbl = Label(self, text="No file selected.")

        self.rangeSimLbl = Label(self, text="# of RTS:")
        self.rangeSim = Entry(self, width=5)
        self.widgetList.append(self.rangeSim)

        self.schedulerLbl = Label(self, text="Scheduler:")
        self.schedulerSelected = None
        self.schedulerComboBox = Combobox(self, textvariable=self.schedulerSelected)
        self.schedulerComboBox['values'] = [*get_schedulers()]
        self.widgetList.append(self.schedulerComboBox)

        self.slackLbl = Label(self, text="Slack method:")
        self.slackListBox = Listbox(self, selectmode=EXTENDED)
        for slackMethod in [*get_slack_methods()]:
            self.slackListBox.insert(END, slackMethod)
        self.widgetList.append(self.slackListBox)

        self.wcetLbl = Label(self, text="Execution type:")
        self.wcetSelected = None
        self.wcetComboBox = Combobox(self, textvariable=self.wcetSelected)
        self.wcetComboBox['values'] = ('WCET', 'ACET', 'BCET')
        self.widgetList.append(self.wcetComboBox)

        self.nInstancesLbl = Label(self, text="# of instances:")
        self.nInstances = Entry(self, width=5)
        self.widgetList.append(self.nInstances)

        self.resultsFrame = Frame(self, relief=SUNKEN)
        self.resultsFrame.grid_rowconfigure(0, weight=1)
        self.resultsFrame.grid_columnconfigure(0, weight=1)
        self.resultsScrollbar = Scrollbar(self.resultsFrame)
        self.resultsTextBox = Text(self.resultsFrame, yscrollcommand=self.resultsScrollbar.set)
        self.resultsScrollbar.config(command=self.resultsTextBox.yview)

        self.errorsFrame = Frame(self, relief=SUNKEN)
        self.errorsFrame.grid_rowconfigure(0, weight=1)
        self.errorsFrame.grid_columnconfigure(0, weight=1)
        self.errorsScrollbar = Scrollbar(self.errorsFrame)
        self.errorsTextBox = Text(self.errorsFrame, yscrollcommand=self.errorsScrollbar.set)
        self.errorsScrollbar.config(command=self.errorsTextBox.yview)

        self.errorReportLbl = Label(self, text="No errors.")

        self.runSimulationButton = Button(self, text="Run simulation", command=self.run_stop_simulation)
        self.progressBar = Progressbar(self, orient=HORIZONTAL, length=100, mode='determinate')
        self.progress_step = 0

        self.saveSimulationResult = Button(self, text="Save Simulation", command=self.save_simulation_results)
        self.widgetList.append(self.saveSimulationResult)

        self.showResultsAsSelected = None
        self.showResultsAsComboBox = Combobox(self, values=print_results_options(), state="readonly",
                                              textvariable=self.showResultsAsSelected)
        self.showResultsAsComboBox.current(0)
        self.showResultsAsComboBox.bind("<<ComboboxSelected>>", self.change_result_presentation)
        self.widgetList.append(self.showResultsAsComboBox)

        self.rowconfigure(0, weight=0, pad=5)
        self.rowconfigure(1, weight=0, pad=5)
        self.rowconfigure(2, weight=0, pad=5)
        self.rowconfigure(3, weight=0, pad=5)
        self.rowconfigure(4, weight=0, pad=5)
        self.rowconfigure(5, weight=3, pad=5)
        self.rowconfigure(6, weight=0, pad=5)
        self.rowconfigure(7, weight=0, pad=5)
        self.rowconfigure(8, weight=0, pad=5)
        self.columnconfigure(0, weight=0, pad=5)
        self.columnconfigure(1, weight=1, pad=5)

        self.openFile.grid(column=0, row=0, sticky="w")
        self.selectedFileLbl.grid(column=1, row=0, sticky="w")
        self.rangeSimLbl.grid(column=4, row=0, sticky="e")
        self.rangeSim.grid(column=5, row=0, sticky="we")
        self.schedulerLbl.grid(column=4, row=1, sticky="e")
        self.schedulerComboBox.grid(column=5, row=1)
        self.slackLbl.grid(column=4, row=2, sticky="e")
        self.slackListBox.grid(column=5, row=2, sticky="we")
        self.wcetLbl.grid(column=4, row=3, sticky="e")
        self.wcetComboBox.grid(column=5, row=3)
        self.nInstancesLbl.grid(column=4, row=4, sticky="e")
        self.nInstances.grid(column=5, row=4, sticky="we")

        self.resultsFrame.grid(column=0, row=1, columnspan=4, rowspan=5, sticky="nesw")
        self.resultsTextBox.pack(side=LEFT, fill=BOTH, expand=1)
        self.resultsScrollbar.pack(side=RIGHT, fill=Y)

        self.errorReportLbl.grid(column=0, row=6, columnspan=3, sticky="nesw")
        self.showResultsAsComboBox.grid(column=3, row=0, sticky="w")

        self.errorsFrame.grid(column=0, row=7, columnspan=4, rowspan=2, sticky="nesw")
        self.errorsTextBox.pack(side=LEFT, fill=BOTH, expand=1)
        self.errorsScrollbar.pack(side=RIGHT, fill=Y)

        self.runSimulationButton.grid(column=5, row=8, sticky="se")
        self.progressBar.grid(column=4, row=9, columnspan=2, sticky="sew")

        self.saveSimulationResult.grid(column=0, row=9, sticky="w")

    def open_file(self):
        self.selectedFile = filedialog.askopenfilename()
        if self.selectedFile:
            self.selectedFileLbl.configure(text=self.selectedFile)

    def save_simulation_results(self):
        return

    def change_result_presentation(self, event):
        self.print_simulation_results()

    def check_inputs(self):
        # Verify that the file exists.
        try:
            os.path.isfile(self.selectedFile)
        except TypeError:
            messagebox.showerror("File", "Invalid file.".format(self.selectedFile))
            return False

        try:
            # Get the number of instances to evaluate.
            if int(self.nInstances.get()) <= 0:
                messagebox.showerror("ERROR", "The number of instances must be greater than 0.")
                return False

            # Get the number of task-set to simulate.
            if int(self.rangeSim.get()) <= 0:
                messagebox.showerror("ERROR", "The number of RTS to simulate must be greater than 0.")
                return False
        except ValueError:
            messagebox.showerror("ERROR", "Invalid number.")
            return False

        # Check the slack methods to evaluate.
        if not len(self.slackListBox.curselection()):
            messagebox.showerror("ERROR", "Select at least one Slack Stealing method.")
            return False

        # All inputs are correct.
        return True

    def get_params(self):
        # Verify user inputs
        if not self.check_inputs():
            return {}

        # Get the file with task-sets.
        # Get the number of instances to evaluate.
        # Get the number of task-set to simulate.
        params = {"file": self.selectedFile, "instance_cnt": int(self.nInstances.get()),
                  "rts_count": int(self.rangeSim.get()), "slack_classes": []}

        # Set the slack methods to evaluate.
        for cur_sel in self.slackListBox.curselection():
            slack_class_key = self.slackListBox.get(cur_sel)
            params["slack_classes"].append(slack_class_key)

        return params

    def run_stop_simulation(self):
        if self.sim_thread is None:
            self.run_simulation()
        else:
            if self.sim_thread.is_alive():
                self.stop_simulation()

    def run_simulation(self):
        # Get params.
        params = self.get_params()
        if not params:
            return

        # Reset progress bar.
        self.progressBar["value"] = 0
        self.progress_step = 100 / int(self.rangeSim.get())

        # Clear results and errors text boxes.
        self.resultsTextBox.delete('1.0', END)
        self.errorsTextBox.delete('1.0', END)

        self.results = []

        # Disable user input widgets.
        self.widget_status(DISABLED)

        # Change button text.
        self.runSimulationButton.config(text="Stop simulation")

        # Initialize Queue.
        self.queue = Queue()

        # Start the simulation thread.
        self.sim_thread = multiprocessing.dummy.Process(target=run_simulation_thread, args=(self.queue, params,))
        self.sim_thread.start()

        # Start the waiting thread.
        self.wait_thread = multiprocessing.dummy.Process(target=self.wait_simulation_thread, args=(params,))
        self.wait_thread.start()

    def stop_simulation(self):
        self.pool.terminate()
        self.queue.close()

    def wait_simulation_thread(self, params):
        # Wait for the results from the simulation processes.
        for _ in range(params["rts_count"]):
            try:
                self.results.append(self.queue.get())  # Could use non-blocking mode.
                self.progressBar["value"] += self.progress_step
                self.progressBar.update()
            except queue.Empty:  # Only when using non-blocking mode.
                pass
            except OSError:  # For Python version > 3.8 should be ValueError.
                break
            except EOFError:  # The queue was closed.
                break

        self.sim_thread = None

        # Change button text.
        self.runSimulationButton.config(text="Run simulation")

        # Reset the progress bar.
        self.progressBar["value"] = 0
        self.progressBar.update()

        # Print results.
        self.print_simulation_results()

        # Enable user input widgets.
        self.widget_status(NORMAL)

    def print_simulation_results(self):
        if self.results is not None:
            results, error_cnt, not_schedulable_cnt, error_list = process_results(self.results, "mean_std")
            self.resultsTextBox.insert(END, print_results(results, print_as=self.showResultsAsComboBox.get(), stdout=False))

    def widget_status(self, status):
        for widget in self.widgetList:
            widget.configure(state=status)


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    return parser.parse_args()


def main():
    gui = MultipleSimulationGui()
    gui.mainloop()


if __name__ == '__main__':
    main()
