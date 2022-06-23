"""
DVS CPU model.
"""


class Cpu:

    def __init__(self, cpuinfo):
        self._cpuinfo = cpuinfo
        self._current_lvl = self.lvls[0]

        for lvl in self.lvls:
            # Calculate ICC
            lvl.append(self.calc_icc(lvl[1]))
            # Power
            lvl.append(lvl[2] * lvl[1])
            # Relative power
            lvl.append(lvl[3] / (self.maxv * self.maxicc))
            # Relative frequency
            #lvl.append(self.lvls[-1][0] / lvl[0])
            lvl.append(self.lvls[-1][0] / lvl[0])
            # Normalize lvl into [0 .. 1]
            lvl.append(lvl[0] / self.lvls[-1][0])

    def calc_icc(self, v):
        M = (self.maxicc - self.minicc) / (self.maxv - self.minv)
        b = (self.maxv * self.minicc - self.minv * self.maxicc) / (self.maxv - self.minv)
        return M * v + b

    def set_lvl(self, new_lvl):
        for lvl in self.lvls:
            if lvl[6] >= new_lvl:
                self._current_lvl = lvl
                return

    @property
    def curlvl(self):
        return self._current_lvl

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

