"""
DVS CPU model.
"""


class Cpu:

    def __init__(self, cpuinfo):
        self._cpuinfo = cpuinfo

    @property
    def numlvls(self):
        return len(self._cpuinfo["lvls"])

    @property
    def maxicc(self):
        return self._cpuinfo["maxicc"]

    @property
    def minicc(self):
        return self._cpuinfo["minicc"]

    @property
    def lvl(self, lvl):
        return self._cpuinfo["lvls"][lvl]

    @property
    def lvls(self):
        return self._cpuinfo["lvls"]






