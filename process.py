#!python

import pandas as pd
import numpy as np
import sys
from argparse import ArgumentParser, FileType


def get_args(options):
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("file", nargs="?", default=sys.stdin, type=FileType('r'), help="File with results.")
    parser.add_argument("--test", type=str, choices=options, default=options[0], help="Test to process.")
    parser.add_argument("--sum", action="store_true", default=False);
    return parser.parse_args()


def main():
    options = ["slack", "sched"]

    args = get_args(options)

    if args.test == options[0]:
        columns = ["Task", "Instance", "cc", "int_length", "slack_calcs", "Method"]
        df = pd.read_csv(sys.stdin, header=None, sep=' ')
        df.columns = columns
        if args.sum:
            print(df.groupby(["Task", "Method"]).sum().to_markdown())
            print(df.groupby(["Method"]).sum().to_markdown())
        else:
            print(df.groupby(["Task", "Method"]).mean().to_markdown())
            print(df.groupby(["Method"]).mean().to_markdown())
    elif args.test == options[1]:
        df = pd.read_csv(sys.stdin, sep='\t')
        print(df.groupby(["Method"]).mean().to_markdown())

if __name__ == '__main__':
    main()
