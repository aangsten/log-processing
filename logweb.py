
import argparse
from typing import List
from flask import render_template
import connexion

from structuredlog import calculate_p95, process, LogEntry, LogType
from exception_entry import ExceptionEntry, get_exceptions
from tool_entry import ToolEntry, get_tools_and_mark_log_entries_with_concurrent_jobs, ToolEntryType, ToolLocationType

# app = Flask(__name__)
app = connexion.App(__name__, specification_dir="./")

log_entries : List[LogEntry] = []
exceptions_sorted : List[ExceptionEntry] = []
tool_entries : List[ToolEntry] = []

@app.route('/')
def route_index():
    context = {
        "exception_sum": sum([len(exception.log_entries) for exception in exceptions_sorted]),
        "p95": calculate_p95(log_entries),
        "started_len": sum(1 for tool in tool_entries if tool.type == ToolEntryType.START ),
        "finished_len": sum(1 for tool in tool_entries if tool.type == ToolEntryType.FINISH ),
        "report_local_deliberate": sum(1 for tool in tool_entries if tool.type == ToolEntryType.START and tool.location == ToolLocationType.LOCAL_DELIBERATE.name ),
        "report_local_unserializable": sum(1 for tool in tool_entries if tool.type == ToolEntryType.START and tool.location == ToolLocationType.LOCAL_UNSERIALIZABLE.name ),
        "report_remote": sum(1 for tool in tool_entries if tool.type == ToolEntryType.START and tool.location == ToolLocationType.REMOTE.name ),
    }

    return render_template("index.html", **context)

@app.route('/exceptions')
def route_exceptions():
    global exceptions_sorted
    return render_template("exceptions.html", exceptions_sorted=exceptions_sorted)

@app.route('/exception-entry/<entry_index>')
def route_exception_entry(entry_index):
    global exceptions_sorted
    return render_template("exception-entry.html", exception=exceptions_sorted[int(entry_index)])

@app.route('/thread-logs/<thread_id>')
def route_thread_logs(thread_id):
    global exceptions_sorted
    thread_log_entries = [entry for entry in log_entries if entry.thread == thread_id]
    return render_template("log-entries.html", log_entries=thread_log_entries, log_filter_id=thread_id, log_type='Thread')

@app.route('/session-logs/<session_id>')
def route_session_logs(session_id):
    global log_entries
    session_log_entries = [entry for entry in log_entries if (entry.type == LogType.RESPONSE or entry.type == LogType.REQUEST) and entry.sessionid == session_id]
    return render_template("log-entries.html", log_entries=session_log_entries, log_filter_id=session_id, log_type='Session')

@app.route('/logs')
def route_logs():
    global log_entries
    return render_template("log-entries.html", log_entries=log_entries, log_filter_id='', log_type='Logs')

@app.route('/tools')
def route_tools():
    started_len = sum(1 for tool in tool_entries if tool.type == ToolEntryType.START )
    finished_len = sum(1 for tool in tool_entries if tool.type == ToolEntryType.FINISH )
    return render_template("tool-entries.html", tool_entries=tool_entries, started_len=started_len, finished_len=finished_len )

@app.route('/performance')
def route_performance():
    global log_entries
    print('log entries')
    print(log_entries)
    return render_template("performance.html", log_entries=log_entries)

def api_logs():
    global log_entries
    return log_entries

def main():
    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('--server', action='store', default='', required=False, help='Wildfly log filename')
    parser.add_argument('--perfmon', action='store', default='', required=False, help='Perfmon4j log filename')
    parser.add_argument('--aspen', action='store', default='', required=False, help='Aspen log filename')
    args = parser.parse_args()
    print(args)
    global log_entries, exceptions_sorted, tool_entries
    log_entries = process(args.server)
    exceptions_sorted = get_exceptions(log_entries)
    tool_entries = get_tools_and_mark_log_entries_with_concurrent_jobs(log_entries)
    print(len(tool_entries))
    # app.add_api("swagger.yaml")
    app.run(debug=True, host='0.0.0.0')

if __name__ == '__main__':
    main()
