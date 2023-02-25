
import argparse
from typing import List
from flask import Flask, render_template

from structuredlog import calculate_p95, process, LogEntry, LogType
from exception_entry import ExceptionEntry, get_exceptions

app = Flask(__name__)
log_entries : List[LogEntry] = []
exceptions_sorted : List[ExceptionEntry] = []


@app.route('/')
def route_index():
    exception_sum = sum([len(exception.log_entries) for exception in exceptions_sorted])
    p95 = calculate_p95(log_entries)
    print( f'p95 {p95}')
    return render_template("index.html", exception_sum=exception_sum, p95=p95)

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

@app.route('/performance')
def route_performance():
    global log_entries
    print('log entries')
    print(log_entries)
    return render_template("performance.html", log_entries=log_entries)


def main():
    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('--server', action='store', default='', required=False, help='Wildfly log filename')
    parser.add_argument('--perfmon', action='store', default='', required=False, help='Perfmon4j log filename')
    parser.add_argument('--aspen', action='store', default='', required=False, help='Aspen log filename')
    args = parser.parse_args()
    print(args)
    global log_entries, exceptions_sorted
    log_entries = process(args.server)
    exceptions_sorted = get_exceptions(log_entries)
    app.run(debug=True, host='0.0.0.0')

if __name__ == '__main__':
    main()
