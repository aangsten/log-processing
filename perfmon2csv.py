import argparse
from collections import defaultdict
from io import TextIOWrapper
import re
import sys
from typing import List
import pandas as pd 
from dateutil.parser import parse

perfmon_logline_pattern = re.compile( '^(?P<log_date>\\d\\d\\d\\d-\\d\\d-\\d\\d) (?P<log_time>\\d\\d:\\d\\d:\\d\\d,\\d+) *\\w+\\s+\\[org.perfmon4j.TextAppender\\] \\(PerfMon.utilityTimer\\)')
#                                                                                                                                    ^- perfmon logger pattern
#                                                                                                                         ^- debug level
#                                      ^- timestamp at beginning of line

sample_range_pattern = re.compile( r'(?P<sample_start>\d\d:\d\d:\d\d):\d\d\d -> (?P<sample_end>\d\d:\d\d:\d\d):\d\d\d' )
#                                                                                                             ^- milliseconds, not collected
#                                                                                   ^- sample end time
#                                                                            ^- arrow to separte start and end
#                                                                     ^- milliseconds, not collected
#                                      ^- sample start time

counter_value_pattern = re.compile( '^ (?P<name>.+)\\. (?P<value>[0-9.-]*)(?P<extra>.*)$')
#                                                                          ^- match everything to end of line
#                                                                ^- match the numeric value
#                                                    ^- the very last period followed by space is the delimiter between name and value
#                                       ^- everything up to the delimiter is name
#                                     ^- first column is the space

class PerfmonEntry:
    def __init__(self, log_date : str, log_time : str):
        self.log_date = log_date
        self.log_time = log_time.replace(',', '.')
        self.counter_name = ''
        self.sample_start = None
        self.sample_end = None
        self.entries = dict()
        self.lifetime_entries = False
        self.names = []

    def to_dict(self):
        values = {
            'log_date': self.log_date,
            'log_time': self.log_time,
            'counter_name' : self.counter_name,
            'sample_start' : f'{self.log_date} {self.sample_start}',
            'sample_end' : f'{self.log_date} {self.sample_end}'
        }
        return values | self.entries

    def process(self, line : str) -> bool:
        if line == '********************************************************************************':
            return len(self.entries) > 0;   # there's two asterisk lines- one at start, one at end.  If we have values, we're done
        if len(self.counter_name) == 0:
            self.counter_name = line
            return False
        if self.sample_start == None:
            range_match = sample_range_pattern.match(line)
            if not range_match:
                raise Exception(f'Unable to parse sample range [{line}]')
            self.sample_start = parse( f"{self.log_date} {range_match.group('sample_start')}" )
            self.sample_end = parse( f"{self.log_date} {range_match.group('sample_end')}" )
            return False
        if line.startswith('Lifetime'):
            self.lifetime_entries = dict()
            return False
        values = counter_value_pattern.match(line)
        if values:
            name = values.group('name').rstrip('.')
            name_extra = name + '_extra'
            self.names.append(name)
            self.names.append(name_extra)
            if len(values.group('value')) > 0:
                self.entries[name] = float(values.group('value')) 
            else:
                self.entries[name] = None
            self.entries[name_extra] = values.group('extra')
            #print (name,'|', values.group('value'))
        else:
            print('bad',line)
        return False

    def print_csv_header(self):
        output = 'counter_name,log_date,log_time,sample_start,sample_end'
        for name in self.names:
            output += ',' + name
        print(output)

    def print_csv(self):
        output = self.counter_name + ',' + self.log_date + ',' + self.log_time + ',' + str(self.sample_start) + ',' + str(self.sample_end)
        for name in self.names:
            output += ',' + str(self.entries[name])
        print(output)



def process_log_line(line : str) -> PerfmonEntry:
    match = perfmon_logline_pattern.match(line)
    if match:
        return PerfmonEntry(match.group('log_date'),match.group('log_time'))
    return None




def process_file(open_file: TextIOWrapper) -> List[PerfmonEntry]:
    perfmon_entry = None
    perfmon_entries : List[PerfmonEntry] = []

    for line in open_file:
        line = line.rstrip()
        if perfmon_entry:
            if perfmon_entry.process(line):
                perfmon_entries.append(perfmon_entry)
                perfmon_entry = None
        else:
            perfmon_entry = process_log_line(line)

    return perfmon_entries

def process_perfmon( file_name : str) -> List[PerfmonEntry]:
    with open(file_name) as open_file:
        return process_file(open_file)

def list_counters(perfmon_entries):
    names = sorted(set(list(map( lambda entry: entry.counter_name, perfmon_entries))))
    for name in names:
        print(name)

def print_csv(perfmon_entries : List[PerfmonEntry], counter_name : str, output_filename : str):
    original_stdout = sys.stdout
    if output_filename :
        sys.stdout = open(output_filename, 'w')
    header_printed = False
    for perfmon_entry in perfmon_entries:
        if perfmon_entry.counter_name == counter_name:
            if not header_printed:
                perfmon_entry.print_csv_header()
                header_printed = True
            perfmon_entry.print_csv()

    if output_filename :
        sys.stdout.close()
        sys.stdout = original_stdout

def perfmon_to_dataframe(perfmon_entries : List[PerfmonEntry], counters):
    df_data = defaultdict(dict)

    # for each perfmon_entry, see if it has each counter.
    for perfmon_entry in perfmon_entries:
        key = perfmon_entry.sample_start
        for counter in counters:
            if counter in perfmon_entry.entries:
                df_data[key][counter] = perfmon_entry.entries[counter]

    sorted_keys = sorted(df_data.keys())
    sorted_data = [df_data[key] for key in sorted_keys ]
    
    df = pd.DataFrame(sorted_data, index=sorted_keys, columns=counters)
    return df

def get_dataframe(perfmon_entries : List[PerfmonEntry]):
    data_lists = defaultdict(list)
    for perfmon_entry in perfmon_entries:
        data_lists[perfmon_entry.counter_name].append(perfmon_entry)
    
    df = pd.DataFrame([i.to_dict() for i in data_lists.values()[0]])

    return df


def main():

    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('filename', type=str, help='Aspen Wildfly  log file' )
    parser.add_argument('-l', '--list', action='store_true', help='Lists perfmon counters' )
    parser.add_argument('--csv', action='store', required=False, help='Counter name to generate CSV')
    parser.add_argument('--output', action='store', default='', required=False, help='Output file name for csv (defaults to stdout)')
    args = parser.parse_args()

    perfmon_entries = process_perfmon(args.filename)
    if args.list:
        list_counters(perfmon_entries)
    if args.csv:
        print_csv(perfmon_entries,args.csv, args.output)

if __name__ == "__main__":
    main()