#!python

from typing import TextIO
from functools import reduce
from schedtests import rta, rta2, rta3, rta4, het2, josephp
from utils import get_rts
import math
import sys

def analyze_rts(rts: list):
    """
    Analyze the RTS u, lcm and schedulability
    :param rts: rts
    :return: None
    """
    rta(rts)
    rta2(rts)
    rta3(rts)
    rta4(rts)
    het2(rts)
    josephp(rts)


def main():
    flag = False

    print("Method\tCC")

    for rts in get_rts(sys.stdin):
        analyze_rts(rts["tasks"])


if __name__ == '__main__':
    main()
