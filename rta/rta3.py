def rta3(rts, rall=True):
    import math

    a = [0] * len(rts)
    i = [0] * len(rts)

    for idx, task in enumerate(rts):
        a[idx] = task["C"]
        i[idx] = task["T"]

    t = rts[0]["C"]
    rts[0]["wcrt"] = t

    for idx, task in enumerate(rts[1:], 1):
        schedulable = True
        t_mas = t + task["C"]

        while schedulable:
            t = t_mas

            for jdx, jtask in zip(range(len(rts[:idx]) - 1, -1, -1), reversed(rts[:idx])):
                if t_mas > i[jdx]:
                    tmp = math.ceil(t_mas / jtask["T"])
                    a_tmp = tmp * jtask["C"]
                    t_mas += (a_tmp - a[jdx])

                    if t_mas > task["D"]:
                        if not rall:
                            return False
                        else:
                            schedulable = False

                    a[jdx] = a_tmp
                    i[jdx] = tmp * jtask["T"]

            if t == t_mas:
                break

        task["wcrt"] = t

    return True
