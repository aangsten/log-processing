
import numpy as np
import pandas as pd
from collections import defaultdict
from typing import List
from structuredlog import LogEntry


# percentile level.  We're interested in response time of 95th percentile
LEVEL = 95
ALL_KEY = 'all'

def get_durations(log_entries : List[LogEntry]) -> dict:
    durations_raw = defaultdict(list)
    for log_entry in log_entries:
        if log_entry.is_response():
            durations_raw[ALL_KEY].append(log_entry.duration)
            durations_raw[log_entry.get_deidentified_path()].append(log_entry.duration)

    return {k: np.array(v) for k, v in durations_raw.items()}

def get_p95(durations: dict):
    return np.percentile(durations[ALL_KEY], LEVEL)

def get_dataframe(durations: dict):
    keys = sorted(durations.keys())

    percentages = [np.percentile(durations[key], LEVEL) for key in keys]
    medians = [np.median(durations[key]) for key in keys]
    counts = [len(durations[key]) for key in keys]
    sums = [sum(durations[key]) for key in keys]

    data = { 'Request' : keys, 'P95' : percentages, 'Median' : medians, 'Count' : counts, 'Sums' : sums}
    df = pd.DataFrame(data)
    return df
