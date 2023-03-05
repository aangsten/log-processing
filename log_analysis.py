
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import List
from structuredlog import LogEntry


# percentile level.  We're interested in response time of 95th percentile
LEVEL = 95
durations_all = np.array([])

def get_durations(log_entries : List[LogEntry]) -> dict:
    durations_raw = defaultdict(list)
    durations_all_raw = []
    for log_entry in log_entries:
        if log_entry.is_response():
            durations_all_raw.append(log_entry.duration)
            durations_raw[log_entry.get_deidentified_path()].append(log_entry.duration)

    global durations_all    #yeah, a side effect from what should be a pure function.  sorry
    durations_all = np.array(durations_all_raw)
    return {k: np.array(v) for k, v in durations_raw.items()}

def get_p95(durations: dict):
    return np.percentile(durations_all, LEVEL)

def get_dataframe(durations: dict):
    keys = sorted(durations.keys())

    percentages = [np.percentile(durations[key], LEVEL) for key in keys]
    medians = [np.median(durations[key]) for key in keys]
    counts = [len(durations[key]) for key in keys]
    sums = [sum(durations[key]) for key in keys]

    data = { 'Request' : keys, 'P95' : percentages, 'Median' : medians, 'Count' : counts, 'Sums' : sums}
    df = pd.DataFrame(data)
    return df
