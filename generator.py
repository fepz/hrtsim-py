from argparse import ArgumentParser, FileType
from simso.generator.task_generator import *
import math

def get_args():
    """ Command line arguments """
    parser = ArgumentParser()
    parser.add_argument("--count", type=int, default=1)
    parser.add_argument("--size", type=int, default=3)
    parser.add_argument("--uf", type=float, default=.7)
    parser.add_argument("--maxt", type=int, default=100)
    return parser.parse_args()

def main():
    args = get_args()
    u = gen_uunifastdiscard(args.count, args.uf, args.size)
    t = gen_periods_uniform(args.size, args.count, 1, args.maxt, True)
    s = gen_tasksets(u, t)
    for taskset in s:
        print(len(taskset))
        ts = [(math.ceil(c), int(t)) for c, t in sorted(taskset, key=lambda x: x[1])]
        for c, t in ts:
            print("{0}\t{1}\t{2}".format(c, t, t))


if __name__ == '__main__':
    main()
