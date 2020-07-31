from argparse import ArgumentParser
from tkinter import Tk
from gui.maingui import MainGui
from cli.SingleSimulation import SingleSimulationCli


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--gui", help="Use GUI.")
    parser.add_argument("--file", type=str, help="File with RTS.")
    parser.add_argument("--rts", type=int, help="RTS number inside file.")
    parser.add_argument("--instance-count", type=int, help="Number of task instances to simulate.")
    parser.add_argument("--ss-method", nargs='+', type=str, help="Slack Stealing method.")
    return parser.parse_args()


def main():
    args = get_args();
    if args.gui:
        root = Tk()
        MainGui(root)
        root.mainloop()
    else:
        cli = SingleSimulationCli(args)
        cli.run_simulation()


if __name__ == '__main__':
    main()
