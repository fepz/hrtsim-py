from tkinter import *
from tkinter import filedialog, messagebox
from tkinter.ttk import Combobox
from tkinter.ttk import Treeview

from resources.xml import load_from_xml
from rta.rta3 import rta3
from schedulers.SchedulerUtil import get_schedulers
from simulations.slack.simslack import run_sim, process_results, print_results
from slack.SlackExceptions import NegativeSlackException
from slack.SlackUtils import get_slack_methods
from tabulate import tabulate


class SingleSimulationGui(Toplevel):

    def __init__(self):
        Toplevel.__init__(self)
        self.title("Single Simulation")
        self.grid()

        self.rts = None

        self.selectedFile = None
        self.openFile = Button(self, text="Open XML file", command=self.open_file)
        self.selectedFileLbl = Label(self, text="File: no file selected.")

        self.selectedRts = Entry(self, width=5)
        self.loadSelectedRts = Button(self, text="Load RTS", command=self.load_table)

        self.schedulerLbl = Label(self, text="Scheduler")
        self.schedulerSelected = None
        self.schedulerComboBox = Combobox(self, textvariable=self.schedulerSelected)
        self.schedulerComboBox['values'] = [*get_schedulers()]

        self.slackLbl = Label(self, text="Slack method")
        self.slackSelected = None
        self.slackComboBox = Combobox(self, textvariable=self.slackSelected)
        self.slackComboBox['values'] = [*get_slack_methods()]

        self.wcetLbl = Label(self, text="Execution type")
        self.wcetSelected = None
        self.wcetComboBox = Combobox(self, textvariable=self.wcetSelected)
        self.wcetComboBox['values'] = ('WCET', 'ACET', 'BCET')

        self.instanceCountLbl = Label(self, text="Instance count")
        self.instanceCount = Entry(self, width=5)

        self.resultsFrame = Frame(self, relief=SUNKEN)
        self.resultsScrollbar = Scrollbar(self.resultsFrame)
        self.resultsTextBox = Text(self.resultsFrame, yscrollcommand=self.resultsScrollbar.set)
        self.resultsScrollbar.config(command=self.resultsTextBox.yview)

        self.runSimulationButton = Button(self, text="Run simulation", command=self.run_simulation)

        tv = Treeview(self)
        tv['columns'] = ('C', 'BC', 'AC', 'T', 'D', 'B', 'J', 'O', 'Co', 'WCRT')
        tv.heading("#0", text='Tarea', anchor='w')
        tv.column("#0", anchor="w")
        tv.heading('C', text='WCET')
        tv.column('C', anchor='center', width=50)
        tv.heading('BC', text='BCET')
        tv.column('BC', anchor='center', width=50)
        tv.heading('AC', text='ACET')
        tv.column('AC', anchor='center', width=50)
        tv.heading('T', text='T')
        tv.column('T', anchor='center', width=50)
        tv.heading('D', text='D')
        tv.column('D', anchor='center', width=50)
        tv.heading('B', text='B')
        tv.column('B', anchor='center', width=50)
        tv.heading('J', text='J')
        tv.column('J', anchor='center', width=50)
        tv.heading('O', text='O')
        tv.column('O', anchor='center', width=50)
        tv.heading('Co', text='Co')
        tv.column('Co', anchor='center', width=50)
        tv.heading('WCRT', text='WCRT')
        tv.column('WCRT', anchor='center', width=50)
        self.treeview = tv

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
        self.selectedRts.grid(column=2, row=0, sticky="e")
        self.loadSelectedRts.grid(column=3, row=0, sticky="e")
        self.treeview.grid(column=0, row=1, columnspan=4, rowspan=5, sticky="nesw")
        self.schedulerLbl.grid(column=4, row=1, sticky="e")
        self.schedulerComboBox.grid(column=5, row=1)
        self.slackLbl.grid(column=4, row=2, sticky="e")
        self.slackComboBox.grid(column=5, row=2)
        self.wcetLbl.grid(column=4, row=3, sticky="e")
        self.wcetComboBox.grid(column=5, row=3)
        self.instanceCountLbl.grid(column=4, row=4, sticky="e")
        self.instanceCount.grid(column=5, row=4, sticky="w")
        self.resultsFrame.grid(column=0, row=6, columnspan=4, rowspan=4, sticky="nesw")
        self.resultsTextBox.pack(side=LEFT, fill=BOTH, expand=1)
        self.resultsScrollbar.pack(side=RIGHT, fill=Y)
        self.runSimulationButton.grid(column=5, row=9, sticky="se")

    def load_table(self):
        try:
            self.rts = load_from_xml(self.selectedFile, int(self.selectedRts.get()))
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
            instance_cnt = int(self.instanceCount.get())
            if instance_cnt <= 0:
                messagebox.showerror("Instance count", "Instance count must be greater than 0.")
                return
        except ValueError:
            messagebox.showerror("Instance count", "Invalid instance count.")
            return

        try:
            params = {
                "instance_cnt": instance_cnt,
                "slack_classes": [self.slackComboBox.get()]
            }

            # Run the simulation.
            sim_result = run_sim(self.rts, params)

            # Clear text box.
            self.resultsTextBox.delete('1.0', END)

            if sim_result["error"]:
                self.resultsTextBox.insert(END, "Simulation failed!\n")
                self.resultsTextBox.insert(END, "\t{0}".format(sim_result["error_msg"]))
            else:
                self.resultsTextBox.insert(END, "Simulation successful!\n")
                self.resultsTextBox.insert(END, "SS CC:\n")
                if instance_cnt < 20:
                    for ss_method, ss_result in sim_result['cc'].items():
                        table_tasks = ["T{:d}".format(n + 1) for n in range(len(ss_result))]
                        self.resultsTextBox.insert(END, "{0}\n".format(ss_method))
                        self.resultsTextBox.insert(END, tabulate(ss_result, showindex=table_tasks,
                                                                 headers=range(1, instance_cnt + 1),
                                                                 tablefmt="github"))

                results, error_cnt, not_schedulable_cnt, error_list = process_results([sim_result], "mean_std")
                self.resultsTextBox.insert(END, print_results(results, stdout=False))

        except NegativeSlackException as exc:
            print(exc)

