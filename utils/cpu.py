"""
DVS CPU model.

0:	Frecuencia
1:	Voltaje
2:	ICC (ampers)
3:	potencia	ampers * voltaje  [unidad jules]
4:	potencia rel
5:	frecuencia rel
6:	normalizado

"""


class Cpu:

    def __init__(self, cpuinfo):
        self._cpuinfo = cpuinfo
        self._current_lvl = self.lvls[0]

        for lvl in self.lvls:
            # Calculate ICC (ampers)
            lvl.append(self.calc_icc(lvl[1]))
            # Power
            lvl.append(lvl[2] * lvl[1])
            # Relative power
            lvl.append(lvl[3] / (self.maxv * self.maxicc))
            # Relative frequency
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

    #def get_adjacent_lvls(self, freq):
    #    for i, lvl in enumerate(self.lvls[1:], start=1):
    #        if lvl[6] >= freq:
    #            return lvl, self.lvls[i - 1]
    def get_adjacent_lvls(self, freq):
        rev_lvls = list(reversed(self.lvls))

        num_lvls = len(self.lvls)
        for i, lvl in enumerate(rev_lvls):
            num_lvls -= 1
            if (freq - lvl[0]) >= 0.00001:
                lvl_i = i
                break
            else:
                pass

        return self.lvls[num_lvls+1], self.lvls[num_lvls]

        #for i, lvl in enumerate(rev_lvls[:-1]):
            #if lvl[6] < freq:
        #    if lvl[6] - freq < 0.0000000000001:
        #        return rev_lvls[i - 1], lvl

        #return self.lvls[1], self.lvls[0]

    def get_lvl_idx(self, freq):
        for i, lvl in enumerate(self.lvls[1:], start=1):
            if lvl[0] >= freq:
                return i - 1, self.lvls[i - 1]

    def get_lvl(self, lvl):
        return self._cpuinfo["lvls"][lvl]

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

