
from datetime import datetime
from collections import namedtuple
import dateparser
import argparse
import pysftp
import re
from dotenv import load_dotenv
import os
from pathlib import Path

Context = namedtuple('Context', 'server output incident_time is_test')


def get_files_in_dir(context: Context, ftp, directory: str, file_pattern: str):
    pattern = re.compile(file_pattern)
    ftp.chdir(directory)
    data = ftp.listdir()
    files = [name for name in data if pattern.match(name)]
    files = sorted(files, reverse=True)
    print('  ' + directory)
    for file in files:
        attr = ftp.stat(file)
        file_mod_time = datetime.fromtimestamp(attr.st_mtime).astimezone()
        # print(file, incident_time, file_mod_time)
        if file_mod_time >= context.incident_time:
            print('    ' + file)
            if not context.is_test:
                ftp.get(file, context.output + '/' + file)
            break
        # break
    ftp.chdir('..')


def get_server_files(context: Context, ftp, cluster_dir: str, server_dir: str):
    print( f'{cluster_dir}/{server_dir}')
    ftp.chdir(server_dir)
    get_files_in_dir(context, ftp, 'aspenlogs', r'^AspenLog[0-9]*\.log.*$')
    get_files_in_dir(context, ftp, 'wildflylogs', r'^server\.log.*$')
    get_files_in_dir(context, ftp, 'wildflylogs', r'^perfmon4j\.log.*$')
    ftp.chdir("..")




def main():

    # command line arguments
    parser = argparse.ArgumentParser(description='Grabs Aspen log files')
    parser.add_argument('--server', action='store', default='', required=True, help='Server name, something like app63 or rpt30.')
    parser.add_argument('--output', action='store', default='.', required=False, help='Local directory to write files to.')
    parser.add_argument('--time', action='store', default='10 min ago', required=False, help='Incident time.  Can be human readable like "30 min ago" or "2 days ago"')
    parser.add_argument('--test', action='store_true', required=False, help='Use this to list files rather than pull them down')
    args = parser.parse_args()

    incident_time : datetime = dateparser.parse(args.time).astimezone()

    context = Context(args.server, args.output, incident_time, args.test)

    #make sure directory exists
    Path(context.output).mkdir(parents=True, exist_ok=True)

    #ftp credentials
    load_dotenv()
    ftp_host = os.getenv('FTP_HOST')
    ftp_user = os.getenv('FTP_USER')
    ftp_password = os.getenv('FTP_PASSWORD')
    if not ftp_host or not ftp_user or not ftp_password:
        print('You must set FTP_HOST, FTP_USER, and FTP_PASSWORD either as environment variables or in the .env file.')
        return
    
    cnopts = pysftp.CnOpts()
    cnopts.hostkeys = None  
    with pysftp.Connection(host=ftp_host, username=ftp_user, password=ftp_password, cnopts=cnopts) as ftp:
        data = ftp.listdir()
        cluster_dirs = [name for name in data if name.startswith('azurec')]
        for cluster_dir in cluster_dirs:
            ftp.chdir(cluster_dir)
            data = ftp.listdir()
            server_dirs = [name for name in data if name.endswith(args.server)]

            for server_dir in server_dirs:
                get_server_files(context, ftp, cluster_dir, server_dir)
            if server_dirs:
                break
            ftp.chdir('..')




if __name__ == '__main__':
    main()
