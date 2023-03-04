from enum import Enum
from typing import List
from structuredlog import process, LogEntry, LogType
import json

class ToolEntryType(Enum):
    START = 1
    FINISH = 2

class ToolLocationType(Enum):
    LOCAL_DELIBERATE = 1 
    LOCAL_UNSERIALIZABLE = 2
    REMOTE = 3

class ToolEntry:
    def __init__(self, entry: LogEntry):
        self.entry = entry
        chunks = entry.message.split(': ', 1)  # format is TOOL (START|FINISH): {json blob}
        self.type = ToolEntryType[chunks[0].lstrip("TOOL ")]
        data = json.loads(chunks[1])
        self.deploymentId = data['deploymentId']
        self.toolId = data['toolId']
        self.toolName = data['toolName']
        self.location = data['location']
        self.duration = data['duration']
        self.parameters = data['parameters']

    def is_start(self):
        return self.type == ToolEntryType.START
    
    def is_finish(self):
        return self.type == ToolEntryType.FINISH

    @classmethod
    def is_tool(cls, entry: LogEntry) -> bool:
        return entry.message.startswith( 'TOOL START:') or entry.message.startswith('TOOL FINISH:')
    

def get_tools(log_entries : List[LogEntry]) -> List[ToolEntry]:
    return [ToolEntry(entry) for entry in log_entries if ToolEntry.is_tool(entry)]

def get_tools_and_mark_log_entries_with_concurrent_jobs(log_entries) -> List[ToolEntry]:
    tool_entries : List[ToolEntry] = []
    running_count = 0   # number of tools "running" right now
    for entry in log_entries:
        if ToolEntry.is_tool(entry):
            tool_entry = ToolEntry(entry)
            tool_entries.append(tool_entry)
            running_count += 1 if tool_entry.is_start() else -1
        entry.concurrent_jobs = running_count
    return tool_entries