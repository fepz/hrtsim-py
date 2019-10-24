from tkinter import *

from gui.SingleSimulation import SingleSimulationGui


class MainGui:

    def __init__(self, master):
        frame = Frame(master)
        frame.pack()
        master.title("HrtSim")

        self.button = Button(frame, text="Single Simulation", command=SingleSimulationGui)
        self.button.pack()
