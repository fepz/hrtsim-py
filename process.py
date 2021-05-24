#!python

import pandas as pd
import numpy as np
import sys

def process_result(model) -> dict:
    import pandas as pd

    cc_df = pd.DataFrame(model.scheduler.data["results"]["ss-cc"])
    cc_df.index.names = ["Task", "Instance"]

    theo_df = pd.DataFrame(model.scheduler.data["results"]["ss-theo"])
    theo_df.index.names = ["Task"]

    return {"cc": cc_df, "theo": theo_df}


def print_means(df) -> None:
    print(df.groupby(["Task", "Method"]).mean().to_markdown())


def print_summary_of_results(results):
    error_list = []
    schedulable_count = 0
    not_schedulable_count = 0
    for result in results:
        if result["schedulable"]:
            schedulable_count += 1
        else:
            not_schedulable_count += 1
            error_list.append("RTS {:d}: not schedulable.".format(result["rts_id"]))
        if result["error"]:
            error_list.append("RTS {:d}: {:s}".format(result["rts_id"], result["error_msg"]))
    print("# of errors: {0:}".format(len(error_list)))
    if error_list:
        for error_msg in error_list:
            print("\t{0:}".format(error_msg))
    print("# of schedulable systems: {0:}".format(schedulable_count))
    print("# of not schedulable systems: {0:}".format(not_schedulable_count))


def main():
    columns = ["Task", "Instance", "tc", "slack", "ttma", "cc", "Method"]
    df = pd.read_csv(sys.stdin, header=None, sep=' ')
    df.columns = columns
    print_means(df)


if __name__ == '__main__':
    main()
