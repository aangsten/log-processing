
from collections import defaultdict
import re
import numpy as np
import argparse
import pandas as pd

response_pattern = re.compile( '^\\d\\d\\d\\d-\\d\\d-\\d\\d.*\t(?P<duration>\\d+)ms\t\S*\t\\d\\d\\d\t(GET|POST|HEAD|DELETE|PATCH)\t(?P<request>[^?\t]+)')
#                                                                                                                                             ^- url up until ?
#                                                                                                    ^- HTTP method
#                                                                                           ^- response code
#                                                                ^- capture 'duration' amount
#                                ^- timestamp at beginning of line

sessionid_pattern = re.compile( 'jsessionid=.*')
oid_pattern = re.compile( '/[a-zA-Z]{3}[a-zA-Z$0-9]{11}/')
oid_other_pattern = re.compile( r'/(banner|assignments|submissions)/.*')

def get_durations(filename : str):
    durations_raw = []
    with open(filename, 'r') as file:
        for line in file:
            match = response_pattern.match(line)
            if match:
                durations_raw.append(int(match.group('duration')))

    return np.array(durations_raw)

def get_split_durations(filename : str, split : bool) -> dict:
    durations_raw = defaultdict(list)
    with open(filename, 'r') as file:
        for line in file:
            # if line.find( '/aspen/rest/') != -1:
            #     print('raw: ' + line)
            match = response_pattern.match(line)
            if match:
                duration = int(match.group('duration'))
                request = match.group('request')
                # if request.find( '/aspen/rest/') != -1:
                #     print('req: ' + request)
                request = re.sub( sessionid_pattern, 'jsessionid', request)
                request = re.sub( oid_pattern, '/*OID*/', request)
                request = re.sub( oid_other_pattern, r'/\1/*OID*', request)
                durations_raw['all'].append(duration)
                if split :
                    durations_raw[request].append(duration)

    return {k: np.array(v) for k, v in durations_raw.items()}

def print_percentile(durations : dict, name : str, level : int):
    value = percentile(durations, level)
    print( f'p{level}: {value: 6,}ms {name}')

def print_percentiles(durations, level : int):
    for key in sorted(durations.keys()):
        print_percentile(durations[key], key, level)

def percentile(durations : dict, level : int):
    return int(np.percentile(durations, level))

def median(durations : dict):
    return int(np.median(durations))

def sum(durations : dict):
    return int(np.sum(durations))

def output_results(durations : dict, level : int):

    keys = sorted(durations.keys())

    percentages = [percentile(durations[key], level) for key in keys]
    medians = [median(durations[key]) for key in keys]
    counts = [len(durations[key]) for key in keys]
    sums = [sum(durations[key]) for key in keys]

    data = { 'Request' : keys, 'P95' : percentages, 'Median' : medians, 'Count' : counts, 'Sums' : sums}
    df = pd.DataFrame(data)
    # df.sort_values(by='P95', inplace=True)
    print(df.to_string(max_rows=None))
    df.to_csv('test.csv')
    print('index',len(df.index))
    # percentages = {k: percentile(v, level) for k, v in durations.items()}
    # del percentages['all']
    # df = pd.DataFrame.from_dict(percentages, orient='index')
    # print('columns')
    # for col in df.columns:
    #     print(f'|{col}|')
    # df.sort_values(0, inplace=True)
    # print(df.to_string())

    print_percentile(durations['all'], 'all', level)

def main():
    parser = argparse.ArgumentParser(description='Reads aspen wildfly log and determines p90, p95, p99 response times')
    parser.add_argument('filename', type=str, help='Aspen Wildfly log file' )
    parser.add_argument('--split', action='store_true', help='Split times out by request type' )
    args = parser.parse_args()

    durations = get_split_durations(args.filename, args.split)
    if len(durations) == 0:
        print('No request durations in log')
    else:
        #print_percentiles(durations, 95)
        output_results(durations, 95)



if __name__ == "__main__":
    main()