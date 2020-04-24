import os
import multiprocessing.dummy
from itertools import repeat
from multiprocessing import Pool, Queue
from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Progressbar

from resources.xml import load_from_xml
from rta.rta3 import rta3
from schedulers.SchedulerUtil import get_schedulers
from simulations.slack.simslack import create_configuration, create_model
from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import get_slack_methods


def run_sim(rts_id, params):
    # Load the rts from file.
    rts = load_from_xml(params["file"], rts_id)

    # Verify that the task-set is schedulable.
    if rta3(rts, True):
        try:
            # Instantiate slack methods.
            slack_methods = []
            for slack_key, slack_class in params["slack_classes"]:
                slack_methods.append(get_class(slack_class)())

            # Create SimSo configuration and model.
            cfg = create_configuration(rts, slack_methods, params["instance_cnt"])
            model = create_model(cfg, slack_methods, params["instance_cnt"])

            # Run the simulation.
            model.run_model()

            # Results
            str_results = {}
            for slack_method in slack_methods:
                slack_method_results = []
                str_results[slack_method.method_name] = slack_method_results
                for task in model.task_list:
                    slack_method_results.append("{}: {}".format(task.name, task.data[slack_method.method_name]["cc"]))

        except NegativeSlackException as exc:
            print(exc)

        run_sim.queue.put(rts_id)

        return [True, str_results]
    else:
        return [False]


def pool_init(r_queue):
    run_sim.queue = r_queue


def get_class(kls):
    parts = kls.split('.')
    module = ".".join(parts[:-1])
    m = __import__(module)
    for comp in parts[1:]:
        m = getattr(m, comp)
    return m


class MultipleSimulationGui(Toplevel):

    def __init__(self):
        Toplevel.__init__(self)
        self.title("Multiple Simulation")
        self.grid()

        # Queue.
        self.queue = Queue()

        # Thread to run the simulations.
        self.t = None

        # List of widgets that can be enabled/disabled.
        self.widgetList = []

        self.selectedFile = None
        self.openFile = Button(self, text="Open XML file", command=self.open_file)
        self.widgetList.append(self.openFile)
        self.selectedFileLbl = Label(self, text="File: no file selected.")

        self.rangeSimLbl = Label(self, text="Number of RTS to simulate:")
        self.rangeSim = Entry(self, width=5)
        self.widgetList.append(self.rangeSim)

        self.schedulerLbl = Label(self, text="Scheduler")
        self.schedulerSelected = None
        self.schedulerComboBox = Combobox(self, textvariable=self.schedulerSelected)
        self.schedulerComboBox['values'] = [*get_schedulers()]
        self.widgetList.append(self.schedulerComboBox)

        self.slackLbl = Label(self, text="Slack method")
        self.slackListBox = Listbox(self, selectmode=EXTENDED)
        for slackMethod in [*get_slack_methods()]:
            self.slackListBox.insert(END, slackMethod)
        self.widgetList.append(self.slackListBox)

        self.wcetLbl = Label(self, text="Execution type")
        self.wcetSelected = None
        self.wcetComboBox = Combobox(self, textvariable=self.wcetSelected)
        self.wcetComboBox['values'] = ('WCET', 'ACET', 'BCET')
        self.widgetList.append(self.wcetComboBox)

        self.nInstancesLbl = Label(self, text="# of instances:")
        self.nInstances = Entry(self, width=5)
        self.widgetList.append(self.nInstances)

        self.resultsFrame = Frame(self, relief=SUNKEN)
        self.resultsScrollbar = Scrollbar(self.resultsFrame)
        self.resultsTextBox = Text(self.resultsFrame, yscrollcommand=self.resultsScrollbar.set)
        self.resultsScrollbar.config(command=self.resultsTextBox.yview)

        self.runSimulationButton = Button(self, text="Run simulation", command=self.run_simulation_action)
        self.widgetList.append(self.runSimulationButton)

        self.progressBar = Progressbar(self, orient=HORIZONTAL, length=100, mode='determinate')
        self.progress_step = 0

        top = self.winfo_toplevel()
        top.rowconfigure(0, weight=0)
        top.columnconfigure(0, weight=0)

        self.rowconfigure(0, weight=0)
        self.rowconfigure(1, weight=0)
        self.rowconfigure(2, weight=0)
        self.rowconfigure(3, weight=0)
        self.rowconfigure(4, weight=1)
        self.rowconfigure(5, weight=1)
        self.columnconfigure(1, weight=1)

        self.openFile.grid(column=0, row=0, sticky="w")
        self.selectedFileLbl.grid(column=1, row=0, sticky="w")
        self.rangeSim.grid(column=3, row=0, sticky="e")
        self.rangeSimLbl.grid(column=2, row=0, sticky="e")
        self.schedulerLbl.grid(column=4, row=1, sticky="e")
        self.schedulerComboBox.grid(column=5, row=1)
        self.slackLbl.grid(column=4, row=2, sticky="e")
        self.slackListBox.grid(column=5, row=2)
        self.wcetLbl.grid(column=4, row=3, sticky="e")
        self.wcetComboBox.grid(column=5, row=3)
        self.nInstancesLbl.grid(column=4, row=4, sticky="e")
        self.nInstances.grid(column=5, row=4, sticky="e")

        self.resultsFrame.grid(column=0, row=1, columnspan=4, rowspan=9, sticky="nesw")
        self.resultsTextBox.pack(side=LEFT, fill=BOTH, expand=1)
        self.resultsScrollbar.pack(side=RIGHT, fill=Y)

        self.runSimulationButton.grid(column=5, row=5, sticky="se")
        self.progressBar.grid(column=4, row=9, columnspan=2, sticky="nesw")

    def open_file(self):
        self.selectedFile = filedialog.askopenfilename()
        self.selectedFileLbl.configure(text="File: " + self.selectedFile)

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
            params["slack_classes"].append((slack_class_key, get_slack_methods()[slack_class_key]))

        return params

    def run_simulation_action(self):
        # Get params.
        params = self.get_params()
        if not params:
            return

        # Reset progress bar.
        self.progressBar["value"] = 0
        self.progress_step = 100 / int(self.rangeSim.get())

        # Clear results text box.
        self.resultsTextBox.delete('1.0', END)

        # Disable user input widgets.
        self.widget_status(DISABLED)

        # Start the simulation thread.
        self.t = multiprocessing.dummy.Process(target=self.run_simulation, args=(self.queue, params,))
        self.t.start()

        # Wait for the results from the simulation processes.
        for _ in range(params["rts_count"]):
            self.queue.get()
            self.progressBar["value"] += self.progress_step
            self.progressBar.update()

        # Enable user input widgets.
        self.widget_status(NORMAL)

    def run_simulation(self, queue, params):
        # List of rts ids to search in the file.
        rts_list = range(1, params["rts_count"] + 1)

        with Pool(initializer=pool_init, initargs=(queue,)) as pool:
            results = pool.starmap(run_sim, zip(rts_list, repeat(params)))

            for result in results:
                if result[0]:
                    for k, v in result[1].items():
                        self.resultsTextBox.insert(END, k + "\n")
                        for r in v:
                            self.resultsTextBox.insert(END, r + "\n")

    def widget_status(self, status):
        for widget in self.widgetList:
            widget.configure(state=status)
