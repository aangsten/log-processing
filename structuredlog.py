from collections import Counter, defaultdict
from enum import Enum
from io import TextIOWrapper
import re
from typing import Dict, List
import numpy as np
import argparse
import pandas as pd
import numpy as np

log_entry_pattern = re.compile( r'^(?P<timestamp>\d\d\d\d-\d\d-\d\d \d\d:\d\d:\d\d,\d\d\d)\s+(?P<level>[A-Z]+)\s+\[(?P<source>[^]]+)\]\s+\((?P<thread>[^)]+)\) (?P<message>.*)$')
#                                                                                                                                                                  ^- rest of line is message
#                                                                                                                                            ^- thread
#                                                                                                                    ^- log source
#                                                                                             ^- debug level - INFO, ERROR, etc
#                                ^- timestamp at beginning of line

guid_pattern = re.compile(r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}')
# guid is pattern of hex digit (0-f) in a pattern of 8-4-4-4-12

request_pattern = re.compile(r'^(?P<tenant>[a-zA-Z-]+)\t(?P<duration>[^\t]+)\t(?P<ipaddr>[0-9.]+)\t(?P<response_code>[0-9-]+)\t(?P<method>[a-zA-Z]+)\t(?P<path>[^\t]+)\t(?P<sessionid>.*)$')
#                                                                                                                                                                        ^- everything else to end of line
#                                                                                                                                                      ^- url path, accepts anything until next tab
#                                                                                                                                 ^- method: letters, e.g. GET, POST, etc
#                                                                                                   ^- response code: numbers or -, e.g. 200, 400, ---
#                                                                               ^- ip address: digits or .
#                                                          ^- duration: everything until next tab.  Expects either --- or ####ms
#                                  ^- tenant: letters or -, e.g. ma-somerset 


class LogType(Enum):
    PLAIN = 1
    REQUEST = 2
    RESPONSE = 3
    EXCEPTION = 4

class LogEntry:

    def __init__(self, match : re.Match[str], line_number : int):
        self.line_number = line_number
        self.timestamp = match.group('timestamp')
        self.level = match.group('level')
        self.source = match.group('source')
        self.thread = match.group('thread')
        self.message = match.group('message')
        self.lines = []
        if self.message.find('Exception') != -1:
            self.type = LogType.EXCEPTION
        else:
            self.type = LogType.PLAIN
            request_match = request_pattern.match(self.message)
            if request_match:
                self.tenant = request_match['tenant']
                duration_str = request_match['duration'].removesuffix('ms')
                if duration_str == '---':
                    self.duration = None
                else:
                    self.duration = int(duration_str)
                self.ipaddr = request_match['ipaddr']
                self.response_code = request_match['response_code']
                self.method = request_match['method']
                self.path = request_match['path']
                self.sessionid = request_match['sessionid']
                if self.response_code == '---':
                    self.type = LogType.REQUEST
                else:
                    self.type = LogType.RESPONSE
            else:
                self.tenant = ''
                self.duration = ''
                self.ipaddr = ''
                self.response_code = ''
                self.method = ''
                self.path = ''
                self.sessionid = ''
                self.type = LogType.PLAIN


    def is_logentry(self, match : re.Match[str]) -> bool:
        return match != None
    
    def get_exception(self):
        if self.type != LogType.EXCEPTION:
            return ''
        text = guid_pattern.sub('GUID', self.message)
        for line in self.caused_by():
            text += '\n\t' + guid_pattern.sub('GUID', line)
        return text

    def caused_by(self) -> List[str]:
        if len(self.lines) == 0:
            return []
        return list(filter( lambda line: line.find('Caused by') != -1, self.lines))

    def dump(self):
        print('>*******************************')
        print( f'timestamp: {self.timestamp}   line: {self.line_number}')
        print( f'level: {self.level}')
        print( f'source: {self.source}')
        print( f'thread: {self.thread}')
        print( f'message: {self.message}')
        cause = self.caused_by()
        if cause:
            print( 'Caused by:')
            for line in cause:
                print( f'\t{line}')
        if self.lines:
            print( 'lines:')
            for line in self.lines:
                print( f'\t{line}')
        print('<*******************************')

    def add_line(self, line):
        self.lines.append(line)


def process_line( log_entries : List[LogEntry], thread_entries, line_number : int, line : str):
    match = log_entry_pattern.match(line)
    if match:
        log = LogEntry(match, line_number)
        if log.message.startswith('\t') and log.thread in thread_entries:
            thread_entries[log.thread].add_line(log.message)
        else:
            log_entries.append(log)
            thread_entries[log.thread] = log
    else:
        if len(log_entries) > 0:
            log_entries[-1].add_line(line)


def process_file(open_file: TextIOWrapper) -> List[LogEntry]:
    log_entry = None
    log_entries : List[LogEntry] = []
    thread_entries = {}

    for line_number, line in enumerate(open_file):
        line = line.rstrip()
        
        process_line(log_entries, thread_entries, line_number + 1, line)

    return log_entries

def process( file_name : str) -> List[LogEntry]:
    if not file_name:
        return []
    with open(file_name) as open_file:
        return process_file(open_file)

def show_exceptions(log_entries : List[LogEntry]):
    counter = Counter()
    for entry in log_entries:
        if entry.message.find('Exception') != -1:
            counter[entry.get_exception()] += 1
    for exception, count in counter.most_common(10):
        print(f"Count: {count} Exception: {exception}")

# given a list of LogEntry, calculate the 95th percentile response time
def calculate_p95(log_entries : List[LogEntry]) -> int:
    times_raw = [log_entry.duration for log_entry in log_entries if log_entry.type == LogType.RESPONSE]
    times = np.array(times_raw)
    return int(np.percentile(times, 95))
    # return 99


def main():

    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('filename', type=str, help='Aspen Wildfly  log file' )
    # parser.add_argument('-l', '--list', action='store_true', help='Lists perfmon counters' )
    # parser.add_argument('--csv', action='store', required=False, help='Counter name to generate CSV')
    # parser.add_argument('--output', action='store', default='', required=False, help='Output file name for csv (defaults to stdout)')
    parser.add_argument('--debug', action='store_true', required=False, help='Dumps debug output')
    parser.add_argument('--exception', action='store_true', required=False, help='Shows exceptions in the log')
    args = parser.parse_args()

    log_entries = process(args.filename)
    if args.debug:
        for entry in log_entries:
            entry.dump()

    if args.exception:
        show_exceptions(log_entries)

    # if args.list:
        # list_counters(perfmon_entries)
    # if args.csv:
        # print_csv(perfmon_entries,args.csv, args.output)

if __name__ == "__main__":
    main()
