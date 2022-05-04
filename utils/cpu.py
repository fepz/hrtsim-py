"""
DVS CPU model.
"""


class Cpu:

    def __init__(self, cpuinfo):
        self._cpuinfo = cpuinfo

        self.lvls[0].append(self.minicc)
        self.lvls[-1].append(self.maxicc)

        for lvl in self.lvls:
            lvl.append(self.calc_icc(lvl[1]))
            lvl.append(lvl[2] * lvl[1])
            lvl.append(lvl[3] / (self.maxv * self.maxicc))
            lvl.append(self.lvls[-1][0] / lvl[0])

    def calc_icc(self, v):
        M = (self.maxicc - self.minicc) / (self.maxv - self.minv)
        b = (self.maxv * self.minicc - self.minv * self.maxicc) / (self.maxv - self.minv)
        return M * v + b

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
    def minv(self):
        return self._cpuinfo["lvls"][0][1]

    @property
    def maxv(self):
        return self._cpuinfo["lvls"][-1][1]

    @property
    def lvl(self, lvl):
        return self._cpuinfo["lvls"][lvl]

    @property
    def lvls(self):
        return self._cpuinfo["lvls"]






