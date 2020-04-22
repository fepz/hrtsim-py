from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox, Progressbar
from tkinter.ttk import Treeview

from resources.xml import load_from_xml
from rta.rta3 import rta3
from schedulers.SchedulerUtil import get_schedulers
from simulations.slack.simslack import create_configuration, create_model
from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import get_slack_methods


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

        self.rts = None

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

        self.runSimulationButton = Button(self, text="Run simulation", command=self.run_simulation)
        self.widgetList.append(self.runSimulationButton)

        self.progressBar = Progressbar(self, orient=HORIZONTAL, length=100, mode='determinate')

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

    def load_table(self):
        try:
            self.rts = load_from_xml(self.selectedFile, int(self.rangeSim.get()))
            # Verify that the task-set is schedulable
            rta3(self.rts, True)
            self.treeview.delete(*self.treeview.get_children())
            for task_id, task in enumerate(self.rts, 1):
                self.treeview.insert("", task_id, text=str(task["nro"]), values=(task["C"], task["BC"], task["AC"],
                                                                                 task["T"], task["D"], task["B"],
                                                                                 task["J"], task["Of"], task["Co"],
                                                                                 task["wcrt"]))
        except ValueError:
            messagebox.showerror("Load RTS", "Invalid RTS number.")
        except TypeError:
            messagebox.showwarning("Load RTS", "No file open.")

    def open_file(self):
        self.selectedFile = filedialog.askopenfilename()
        self.selectedFileLbl.configure(text="File: " + self.selectedFile)

    def run_simulation(self):
        # Get the number of instances to evaluate.
        try:
            instance_cnt = int(self.nInstances.get())
            if instance_cnt <= 0:
                messagebox.showerror("Instance count", "Instance count must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Instance count", "Invalid instance count.")
            return

        # Set the slack methods to evaluate.
        slack_methods = []
        for cursel in self.slackListBox.curselection():
            slack_class_key = self.slackListBox.get(cursel)
            slack_class = get_slack_methods()[slack_class_key]
            slack_methods.append(get_class(slack_class)())

        # Get the number of task-set to simulate.
        rts_count = int(self.rangeSim.get())

        # Reset progress bar.
        self.progressBar["value"] = 0
        progress_step = 100 / rts_count
        progress = 0

        # Clear results text box.
        self.resultsTextBox.delete('1.0', END)

        self.widgetStatus(DISABLED)

        # Simulate the first rts_count task-sets.
        for rts_number in range(rts_count):
            # Load the rts from file.
            rts = load_from_xml(self.selectedFile, int(self.rangeSim.get()))

            # Verify that the task-set is schedulable.
            schedulable = rta3(rts, True)

            if schedulable:
                try:
                    # Create SimSo configuration and model.
                    cfg = create_configuration(rts, slack_methods, instance_cnt)
                    model = create_model(cfg, slack_methods, instance_cnt)

                    # Run the simulation.
                    model.run_model()

                    # Print results in the text box.
                    self.resultsTextBox.insert(END, "RTS {:d} simulated successfully.\n".format(rts_number))
                    for slack_method in slack_methods:
                        for task in model.task_list:
                            cc_str = "{}: {}\n".format(task.name, task.data[slack_method.method_name]["cc"])
                            self.resultsTextBox.insert(END, cc_str)

                    # Updates progress bar.
                    progress = progress + progress_step
                    self.progressBar['value'] = progress
                    self.progressBar.update()

                except NegativeSlackException as exc:
                    print(exc)
            else:
                self.resultsTextBox.insert(END, "RTS {:d} not schedulable.\n".format(rts_number))

        self.widgetStatus(NORMAL)

    def widgetStatus(self, status):
        for widget in self.widgetList:
            widget.configure(state=status)
