from argparse import ArgumentParser, FileType
import sys


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--gui", action='store_true', help="Use GUI.")
    parser.add_argument("--file", type=FileType('r'), help="File with RTS.")
    parser.add_argument("--rts", type=str, help="RTS number inside file.")
    parser.add_argument("--scheduler", nargs=1, type=str, help="Scheduling algorithm")
    parser.add_argument("--instance-count", type=int, help="Number of task instances to simulate.")
    parser.add_argument("--ss-methods", nargs='+', type=str, help="Slack Stealing methods.")
    parser.add_argument("--silent", action="store_true", help="Suppress output.")
    parser.add_argument("--multiple", action="store_true", help="Multiple RTS simulation.")
    parser.add_argument("--gantt-gui", action="store_true", help="Show gantt of scheduling.")
    return parser.parse_args()


def main():
    if not len(sys.argv) > 1:
        print("No arguments!", file=sys.stderr)
        exit()

    args = get_args()
    if args.gui:
        from tkinter import Tk
        from gui.maingui import MainGui
        root = Tk()
        MainGui(root)
        root.mainloop()
    else:
        from cli import cli
        cli.run_simulation(args)


if __name__ == '__main__':
    main()
