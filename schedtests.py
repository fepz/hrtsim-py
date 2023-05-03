import math

def josephp(rts: list):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    schedulable = True

    rts[0]["R"] = rts[0]["C"]
    for i, task in enumerate(rts[1:], 1):
        r = 1
        c, t, d = task["C"], task["T"], task["D"]
        while schedulable:
            w = 0
            for taskp in rts[:i]:
                cp, tp = taskp["C"], taskp["T"]
                w += ceil(float(r) / float(tp)) * cp
            w = c + w
            if r == w:
                break
            r = w
            if r > d:
                schedulable = False
        task["R"] = r

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def josephp_u(rts: list):
    """ Calcula el WCRT de cada tarea del str y evalua la planificabilidad """
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)

    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    schedulable = True

    rts[0]["R"] = rts[0]["C"]
    for i, task in enumerate(rts[1:], 1):
        r = 1
        c, t, d = task["C"], task["T"], task["D"]
        while schedulable:
            w = 0

            # reversed list (from lower to higher priority)
            task_list = [(jdx, jtask, jtask["C"] / jtask["T"]) for jdx, jtask in enumerate(rts[:i])]

            # now sort the reversed list from higher uf to lower uf
            uf_sorted_list = sorted(task_list, key=lambda item: item[2], reverse=True)

            #for taskp in rts[:i]:
            for _, taskp, _ in uf_sorted_list:
                cp, tp = taskp["C"], taskp["T"]
                w += ceil(float(r) / float(tp)) * cp
            w = c + w
            if r == w:
                break
            r = w
            if r > d:
                schedulable = False
        task["R"] = r

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    schedulable = True

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while schedulable:
            t = t_mas
            w = task["C"]

            loops[idx] += 1
            while_loops[idx] += 1

            for jdx, jtask in enumerate(rts[:idx]):
                loops[idx] += 1
                for_loops[idx] += 1

                w += ceil(t_mas / jtask["T"]) * jtask["C"]

                ceils[idx] += 1

                if w > task["D"]:
                    schedulable = False
                    break

            t_mas = w

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, loops, for_loops, while_loops]


def rta_uf(rts, verbose=True):
    """
    RTA con la modificación en el orden de las tareas el sumatoria (por FU)
    """

    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    schedulable = True

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while schedulable:
            t = t_mas
            w = task["C"]

            loops[idx] += 1
            while_loops[idx] += 1

            # reversed list (from lower to higher priority)
            task_list = [(jdx, jtask, jtask["C"] / jtask["T"]) for jdx, jtask in enumerate(rts[:idx])]

            # now sort the reversed list from higher uf to lower uf
            uf_sorted_list = sorted(task_list, key=lambda item: item[2], reverse=True)

            #for jdx, jtask in enumerate(rts[:idx]):
            for jdx, jtask, _ in uf_sorted_list:
                loops[idx] += 1
                for_loops[idx] += 1

                w += ceil(t_mas / jtask["T"]) * jtask["C"]

                ceils[idx] += 1

                if w > task["D"]:
                    schedulable = False
                    break

            t_mas = w

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta2(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while schedulable:
            t = t_mas

            loops[idx] += 1
            while_loops[idx] += 1

            for jdx, jtask in enumerate(rts[:idx]):
                loops[idx] += 1
                for_loops[idx] += 1

                tmp = ceil(t_mas / jtask["T"])
                a_tmp = tmp * jtask["C"]

                t_mas += (a_tmp - a[jdx])
                ceils[idx] += 1

                if t_mas > task["D"]:
                    schedulable = False
                    break

                a[jdx] = a_tmp

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta2u(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while schedulable:
            t = t_mas

            loops[idx] += 1
            while_loops[idx] += 1

            # reversed list (from lower to higher priority)
            task_list = [(jdx, jtask, jtask["C"] / jtask["T"]) for jdx, jtask in enumerate(rts[:idx])]

            # now sort the reversed list from higher uf to lower uf
            uf_sorted_list = sorted(task_list, key=lambda item: item[2], reverse=True)

            #for jdx, jtask in enumerate(rts[:idx]):
            for jdx, jtask, _ in uf_sorted_list:
                loops[idx] += 1
                for_loops[idx] += 1

                tmp = ceil(t_mas / jtask["T"])
                a_tmp = tmp * jtask["C"]

                t_mas += (a_tmp - a[jdx])
                ceils[idx] += 1

                if t_mas > task["D"]:
                    schedulable = False
                    break

                a[jdx] = a_tmp

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta3(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    i = [0] * len(rts)
    schedulable = True
    flag = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while schedulable:
            t = t_mas

            loops[idx] += 1
            while_loops[idx] += 1

            for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx])):
                loops[idx] += 1
                for_loops[idx] += 1
                
                if t_mas > i[jdx]:
                    tmp = ceil(t_mas / jtask["T"])
                    a_tmp = tmp * jtask["C"]

                    t_mas += (a_tmp - a[jdx])
                    ceils[idx] += 1
                    
                    if t_mas > task["D"]:
                        schedulable = False
                        break

                    a[jdx] = a_tmp
                    i[jdx] = tmp * jtask["T"]

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta4(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    i = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]

    t_mas = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    min_i = i[0]

    for idx, task in enumerate(rts[1:], 1):
        t_mas += task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while t_mas > min_i:
            min_i = i[idx]

            loops[idx] += 1
            while_loops[idx] += 1


            for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx])):
                loops[idx] += 1
                for_loops[idx] += 1

                if t_mas > i[jdx]:
                    dif_a = t_mas - a[jdx]
                    a_mas_1 = ceil(dif_a / (jtask["T"] - jtask["C"]))
                    ceils[idx] += 1

                    t_mas = (a_mas_1 * jtask["C"]) + dif_a

                    a[jdx] = a_mas_1 * jtask["C"]
                    i[jdx] = a_mas_1 * jtask["T"]

                    if t_mas > task["D"]:
                        schedulable = False
                        break

                if min_i > i[jdx]:
                    min_i = i[jdx]

            if not schedulable:
                break

        wcrt[idx] = t_mas

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def het2(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    def workload(i, b, n):
        loops[n] += 1
        while_loops[n] += 1

        f = floor(b / rts[i]["T"])
        c = ceil(b / rts[i]["T"])

        ceils[n] += 2

        branch0 = b - f * (rts[i]["T"] - rts[i]["C"])
        branch1 = c * rts[i]["C"]

        if i > 0:
            l_w = last_workload[i - 1]
            tmp = f * rts[i]["T"]
            if tmp > last_psi[i - 1]:
                l_w = workload(i - 1, tmp, n)

            branch0 += l_w
            branch1 += workload(i - 1, b, n)

        last_psi[i] = b
        last_workload[i] = branch0 if branch0 <= branch1 else branch1

        return last_workload[i]

    # metrics
    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    last_psi = [0] * len(rts)
    last_workload = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    trace_string = []
    schedulable = True

    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        loops[idx] += 1
        for_loops[idx] += 1
        w = workload(idx - 1, task["D"], idx)
        if w + task["C"] > task["D"]:
            schedulable = False
            break
        wcrt[idx] = w + task["C"]

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def het2u(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    def workload(i, b, n):
        loops[n] += 1
        while_loops[n] += 1

        f = floor(b / rts[i]["T"])
        c = ceil(b / rts[i]["T"])

        ceils[n] += 2

        branch0 = b - f * (rts[i]["T"] - rts[i]["C"])
        branch1 = c * rts[i]["C"]

        if i > 0:
            l_w = last_workload[i - 1]
            tmp = f * rts[i]["T"]
            if tmp > last_psi[i - 1]:
                l_w = workload(i - 1, tmp, n)

            branch0 += l_w
            branch1 += workload(i - 1, b, n)

        last_psi[i] = b
        last_workload[i] = branch0 if branch0 <= branch1 else branch1

        return last_workload[i]

    # metrics
    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    last_psi = [0] * len(rts)
    last_workload = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    trace_string = []
    schedulable = True

    wcrt[0] = rts[0]["C"]

    reversed_list = [(jdx, jtask, jtask["C"] / jtask["T"]) for jdx, jtask in enumerate(rts[1:], 1)]

    uf_sorted_list = sorted(reversed_list, key=lambda item: item[2], reverse=True)

    #for idx, task in enumerate(rts[1:], 1):
    for idx, task, _ in uf_sorted_list:
        loops[idx] += 1
        for_loops[idx] += 1
        w = workload(idx - 1, task["D"], idx)
        if w + task["C"] > task["D"]:
            schedulable = False
            break
        wcrt[idx] = w + task["C"]

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta3u(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    i = [0] * len(rts)
    c = [0] * len(rts)
    schedulable = True
    flag = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]
        task["U"] = task["C"] / task["T"]

    t = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    for idx, task in enumerate(rts[1:], 1):
        t_mas = t + task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while schedulable:
            t = t_mas

            loops[idx] += 1
            while_loops[idx] += 1

            reversed_list = [(jdx, jtask, jtask["C"] / jtask["T"]) for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx]))]

            uf_sorted_list = sorted(reversed_list, key=lambda item: item[2], reverse=True)

            for jdx, jtask, _ in uf_sorted_list:
                loops[idx] += 1
                for_loops[idx] += 1
                
                if t_mas > i[jdx]:
                    tmp = ceil(t_mas / jtask["T"])
                    a_tmp = tmp * jtask["C"]

                    t_mas += (a_tmp - a[jdx])
                    ceils[idx] += 1
                    
                    if t_mas > task["D"]:
                        schedulable = False
                        break

                    a[jdx] = a_tmp
                    i[jdx] = tmp * jtask["T"]

            if t == t_mas:
                break

        wcrt[idx] = t

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]



def rta4u(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    i = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]

    t_mas = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    min_i = i[0]

    for idx, task in enumerate(rts[1:], 1):
        t_mas += task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while t_mas > min_i:
            min_i = i[idx]

            loops[idx] += 1
            while_loops[idx] += 1

            # reversed list (from lower to higher priority)
            reversed_list = [(jdx, jtask, jtask["C"] / jtask["T"]) for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx]))]

            # now sort the reversed list from higher uf to lower uf
            uf_sorted_list = sorted(reversed_list, key=lambda item: item[2], reverse=True)

            #for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx])):
            for jdx, jtask, _ in uf_sorted_list:
                loops[idx] += 1
                for_loops[idx] += 1

                if t_mas > i[jdx]:
                    dif_a = t_mas - a[jdx]
                    a_mas_1 = ceil(dif_a / (jtask["T"] - jtask["C"]))
                    ceils[idx] += 1

                    t_mas = (a_mas_1 * jtask["C"]) + dif_a

                    a[jdx] = a_mas_1 * jtask["C"]
                    i[jdx] = a_mas_1 * jtask["T"]

                    if t_mas > task["D"]:
                        schedulable = False
                        break

                if min_i > i[jdx]:
                    min_i = i[jdx]

            if not schedulable:
                break

        wcrt[idx] = t_mas

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta4a(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    i = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]

    for task in rts:
        task["holgura"] = task["T"] - task["C"]

    t_mas = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    min_i = i[0]

    for idx, task in enumerate(rts[1:], 1):
        t_mas += task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while t_mas > min_i:
            min_i = i[idx]

            loops[idx] += 1
            while_loops[idx] += 1

            # reversed list (from lower to higher priority)
            reversed_list = [(jdx, jtask) for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx]))]

            # now sort the reversed list from higher uf to lower uf
            uf_sorted_list = sorted(reversed_list, key=lambda item: item[1]["holgura"], reverse=True)

            for jdx, jtask in uf_sorted_list:
                loops[idx] += 1
                for_loops[idx] += 1

                if t_mas > i[jdx]:
                    dif_a = t_mas - a[jdx]
                    a_mas_1 = ceil(dif_a / (jtask["T"] - jtask["C"]))
                    ceils[idx] += 1

                    t_mas = (a_mas_1 * jtask["C"]) + dif_a

                    a[jdx] = a_mas_1 * jtask["C"]
                    i[jdx] = a_mas_1 * jtask["T"]

                    if t_mas > task["D"]:
                        schedulable = False
                        break

                if min_i > i[jdx]:
                    min_i = i[jdx]

            if not schedulable:
                break

        wcrt[idx] = t_mas

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]


def rta8(rts):
    def cc_counter(fn):
        def wrapper(*args, **kwargs):
            wrapper.counter += 1
            return fn(*args, **kwargs)
        wrapper.counter = 0
        wrapper.__name__ = fn.__name__
        return wrapper

    @cc_counter
    def ceil(v):
        return math.ceil(v)

    @cc_counter
    def floor(v):
        return math.floor(v)


    wcrt = [0] * len(rts)
    ceils = [0] * len(rts)
    loops = [0] * len(rts)
    for_loops = [0] * len(rts)
    while_loops = [0] * len(rts)
    a = [0] * len(rts)
    i = [0] * len(rts)
    schedulable = True

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]

    t_mas = rts[0]["C"]
    wcrt[0] = rts[0]["C"]

    min_i = i[0]

    for idx, task in enumerate(rts[1:], 1):
        t_mas += task["C"]

        loops[idx] += 1
        for_loops[idx] += 1

        while t_mas > min_i:
            min_i = i[idx]

            loops[idx] += 1
            while_loops[idx] += 1

            # reversed list (from lower to higher priority)
            reversed_list = [(jdx, jtask, a[jdx]) for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx]))]

            # now sort the reversed list from higher uf to lower uf
            uf_sorted_list = sorted(reversed_list, key=lambda item: item[2], reverse=True)

            #for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx])):
            for jdx, jtask, _ in uf_sorted_list:
                loops[idx] += 1
                for_loops[idx] += 1

                if t_mas > i[jdx]:
                    dif_a = t_mas - a[jdx]
                    a_mas_1 = ceil(dif_a / (jtask["T"] - jtask["C"]))
                    ceils[idx] += 1

                    t_mas = (a_mas_1 * jtask["C"]) + dif_a

                    a[jdx] = a_mas_1 * jtask["C"]
                    i[jdx] = a_mas_1 * jtask["T"]

                    if t_mas > task["D"]:
                        schedulable = False
                        break

                if min_i > i[jdx]:
                    min_i = i[jdx]

            if not schedulable:
                break

        wcrt[idx] = t_mas

        if not schedulable:
            wcrt[idx] = 0
            break

    return [schedulable, wcrt, floor.counter + ceil.counter, ceils, loops, for_loops, while_loops]
