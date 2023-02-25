
from typing import List
from structuredlog import process, LogEntry, LogType



class ExceptionEntry:
    def __init__(self, entry: LogEntry):
        self.log_entries = [entry]
        self.text = entry.get_exception()

    def __lt__(self, obj):
        if len(self.log_entries) == len(obj.log_entries):
            return self.text < obj.text
        return len(self.log_entries) < len(obj.log_entries)

    def add_log(self, entry : LogEntry):
        self.log_entries.append(entry)


def get_exceptions(log_entries : List[LogEntry]) -> List[ExceptionEntry]:
    exceptions = dict()

    for log_entry in log_entries:
        if log_entry.type == LogType.EXCEPTION:
            text = log_entry.get_exception()
            if  text in exceptions:
                exceptions[text].add_log(log_entry)
            else:
                exceptions[text] = ExceptionEntry(log_entry)
    
    _ = [value for key, value in exceptions.items()]
    return sorted(_, reverse=True)

