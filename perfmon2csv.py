import argparse
from io import TextIOWrapper
import re
import sys
from typing import List

perfmon_logline_pattern = re.compile( '^(?P<timestamp>\\d\\d\\d\\d-\\d\\d-\\d\\d \\d\\d:\\d\\d:\\d\\d,\\d+) *\\w+\\s+\\[org.perfmon4j.TextAppender\\] \\(PerfMon.utilityTimer\\)')
#                                                                                                                     ^- perfmon pattern
#                                                                                                            ^- debug level
#                                      ^- timestamp at beginning of line

counter_value_pattern = re.compile( '^ (?P<name>.+)\\. (?P<value>[0-9.-]*)(?P<extra>.*)$')
#                                                                          ^- match everything to end of line
#                                                                ^- match the numeric value
#                                                    ^- the very last period followed by space is the delimiter between name and value
#                                       ^- everything up to the delimiter is name
#                                     ^- first column is the space

class PerfmonEntry:
    def __init__(self, timestamp : str):
        self.timestamp = timestamp.replace(',', '.')
        self.counter_name = ''
        self.sample_range = ''
        self.entries = dict()
        self.lifetime_entries = False
        self.names = []

    def process(self, line : str) -> bool:
        if line == '********************************************************************************':
            return len(self.entries) > 0;   # there's two asterisk lines- one at start, one at end.  If we have values, we're done
        if len(self.counter_name) == 0:
            self.counter_name = line
            return False
        if len(self.sample_range) == 0:
            self.sample_range = line
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
            self.entries[name] = values.group('value')
            self.entries[name_extra] = values.group('extra')
            #print (name,'|', values.group('value'))
        else:
            print('bad',line)
        return False

    def print_csv_header(self):
        output = 'counter_name,timestamp,time_range'
        for name in self.names:
            output += ',' + name
        print(output)

    def print_csv(self):
        output = self.counter_name + ',' + self.timestamp + ',' + self.sample_range
        for name in self.names:
            output += ',' + self.entries[name]
        print(output)



def process_log_line(line : str) -> PerfmonEntry:
    match = perfmon_logline_pattern.match(line)
    if match:
        return PerfmonEntry(match.group('timestamp'))
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

def process( file_name : str) -> List[PerfmonEntry]:
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

def main():

    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('filename', type=str, help='Aspen Wildfly  log file' )
    parser.add_argument('-l', '--list', action='store_true', help='Lists perfmon counters' )
    parser.add_argument('--csv', action='store', required=False, help='Counter name to generate CSV')
    parser.add_argument('--output', action='store', default='', required=False, help='Output file name for csv (defaults to stdout)')
    args = parser.parse_args()

    perfmon_entries = process(args.filename)
    if args.list:
        list_counters(perfmon_entries)
    if args.csv:
        print_csv(perfmon_entries,args.csv, args.output)

if __name__ == "__main__":
    main()