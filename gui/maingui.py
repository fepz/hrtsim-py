from tkinter import *

from gui.SingleSimulation import SingleSimulationGui
from gui.MultipleSimulationGui import MultipleSimulationGui

class MainGui:

    def __init__(self, master):
        frame = Frame(master)
        frame.pack()
        master.title("HrtSim")

        self.singleSimButton = Button(frame, text="Single Simulation", command=SingleSimulationGui)
        self.singleSimButton.pack()
        self.multipleSimButton = Button(frame, text="Multiple Simulation", command=MultipleSimulationGui)
        self.multipleSimButton.pack()
