from pydantic import BaseModel
from io import TextIOWrapper
import re
import argparse
from typing import Dict, List

aspen_log_entry_pattern = re.compile( r'^(?P<timestamp>\d+-\d+-\d+ \d+:\d+:\d+ .\d+)\s(?P<level>[a-zA-Z0-9]+):\s+\[(?P<source>[^]]+)]\s+\[(?P<logtype>[^]]+)]\s(?P<remainder>.*)')

message_id_pattern = re.compile(r'^(?P<id>[A-Z]{3}-\d{5}):\s*(?P<message>.*)$')

class AspenLogEntry(BaseModel):
    timestamp: str
    level: str
    source: str
    logtype: str
    id: str
    message: str
    lines: list[str]

    @classmethod
    def from_match(cls, match:re.Match[str]):
        timestamp = match.group('timestamp')
        level = match.group('level')
        source = match.group('source')
        logtype = match.group('logtype')
        remainder = match.group('remainder')

        match = message_id_pattern.match(remainder)
        if match:
            id = match.group('id')
            message = match.group('message')
        else:
            id = ''
            message = remainder

        return cls(timestamp=timestamp, level=level, source=source, logtype=logtype, id=id, message=message, lines=[])
        # print('timestamp',self.timestamp)
        # print('level', self.level)
        # print('source', self.source)
        # print('logtype', self.logtype)
        # print('id', self.id)
        # print('message', self.message)


def process_file(open_file: TextIOWrapper) -> List[AspenLogEntry]:
    log_entry = None
    log_entries : List[AspenLogEntry] = []

    for line_number, line in enumerate(open_file):
        line = line.rstrip()
        match = aspen_log_entry_pattern.match(line)
        if match:
            entry = AspenLogEntry.from_match(match)
            log_entries.append(entry)
        elif len(log_entries) > 0:
            log_entries[-1].lines.append(line)
        else:
            print("Whups, error, looks like continuation of log entry before we've had log entry")

    return log_entries

def process_aspenlog( file_names : List[str]) -> List[AspenLogEntry]:
    if not file_names:
        return []
    
    list = []
    for file_name in file_names:
        with open(file_name) as open_file:
            list.extend(process_file(open_file))
            print('list len ', len(list))
    list.sort(key=lambda x: x.timestamp)
    return list

def main():

    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('filename', type=str, help='Aspen Wildfly  log file' )
    parser.add_argument('--debug', action='store_true', required=False, help='Dumps debug output')
    args = parser.parse_args()

    log_entries = process_aspenlog([args.filename])
    # if args.debug:
    #     for entry in log_entries:
    #         entry.dump()


if __name__ == "__main__":
    main()
