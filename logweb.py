
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
    return render_template("index.html")

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
    return render_template("thread-logs.html", log_entries=log_entries, thread_id=thread_id)

@app.route('/logs')
def route_logs():
    return render_template("logs.html")

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
    parser.add_argument('filename', type=str, help='Aspen Wildfly  log file' )
    args = parser.parse_args()
    global log_entries
    log_entries = process(args.filename)
    global exceptions_sorted
    exceptions_sorted = get_exceptions(log_entries)
    app.run(debug=True, host='0.0.0.0')

if __name__ == '__main__':
    main()
