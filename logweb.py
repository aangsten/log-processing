
import argparse
from typing import List
from flask import Flask, render_template

from structuredlog import process, LogEntry, LogType

app = Flask(__name__)
log_entries = []
exceptions = dict()
exceptions_sorted = []

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



@app.route('/')
def route_index():
    exception_sum = sum([len(exception.log_entries) for exception in exceptions_sorted])
    return render_template("index.html", exception_sum=exception_sum)

@app.route('/exceptions')
def route_exceptions():
    global exceptions_sorted
    return render_template("exceptions.html", exceptions_sorted=exceptions_sorted)

@app.route('/exception-entry/<entry_index>')
def route_exception_entry(entry_index):
    global exceptions_sorted
    print(exceptions_sorted[int(entry_index)])
    return render_template("exception-entry.html", exception=exceptions_sorted[int(entry_index)])

@app.route('/thread-logs/<thread_id>')
def route_thread_logs(thread_id):
    global exceptions_sorted
    thread_log_entries = [entry for entry in log_entries if entry.thread == thread_id]
    return render_template("thread-logs.html", log_entries=thread_log_entries, thread_id=thread_id)

@app.route('/logs')
def route_logs():
    return render_template("logs.html")

@app.route('/performance')
def route_performance():
    return render_template("performance.html")

def get_exceptions(log_entries):
    for log_entry in log_entries:
        if log_entry.type == LogType.EXCEPTION:
            text = log_entry.get_exception()
            if  text in exceptions:
                exceptions[text].add_log(log_entry)
            else:
                exceptions[text] = ExceptionEntry(log_entry)
    
    _ = [value for key, value in exceptions.items()]
    return sorted(_, reverse=True)


def main():
    parser = argparse.ArgumentParser(description='Reads log file and extracts ')
    parser.add_argument('--server', action='store', default='', required=False, help='Wildfly log filename')
    parser.add_argument('--perfmon', action='store', default='', required=False, help='Perfmon4j log filename')
    parser.add_argument('--aspen', action='store', default='', required=False, help='Aspen log filename')
    args = parser.parse_args()
    print(args)
    global log_entries
    log_entries = process(args.server)
    global exceptions_sorted
    exceptions_sorted = get_exceptions(log_entries)
    app.run(debug=True, host='0.0.0.0')

if __name__ == '__main__':
    main()
