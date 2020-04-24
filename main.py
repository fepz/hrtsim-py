from argparse import ArgumentParser
from tkinter import Tk
from gui.maingui import MainGui


def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    return parser.parse_args()


def main():
    root = Tk()
    gui = MainGui(root)
    root.mainloop()


if __name__ == '__main__':
    main()
