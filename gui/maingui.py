from tkinter import Frame, Label, Button
from gui.SingleSimulation import SingleSimulationGui
from gui.MultipleSimulationGui import MultipleSimulationGui


class MainGui:

    def __init__(self, master):
        frame = Frame(master)
        frame.pack()
        master.title("HrtSimPy")

        self.titleLabel = Label(frame, text="HrtSim v2").pack()
        self.singleSimButton = Button(frame, text="Single Simulation", command=SingleSimulationGui).pack()
        self.multipleSimButton = Button(frame, text="Multiple Simulation", command=MultipleSimulationGui).pack()
