#!/usr/bin/env python

from __future__ import print_function
import subprocess
import re
import time
import signal 
import sys

class bc:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class FilesMonitor(object): 
    """A simple class for tracking the TCP/UDP connections and open files of a process

    Arguments: 

    pid: the process ID to track

    no_plot: skip making the plot at the end (useful if no matplotlib present)

    quiet: don't litter on the console

    delay: how frequently to look for updates

    file: a file specifying a group of PIDs to track, one per line
    """

    pid = None
    times = []
    data = {'connections':[], 'files':[]}

    def __init__(self, pid, no_plot, quiet, delay, file = None): 
        self.pid = pid
        self.no_plot = no_plot
        self.quiet = quiet
        self.delay = delay
        self.file = file

        signal.signal(signal.SIGINT, self.signal_handler)

    @staticmethod
    def get_open_files(pid):
        """Return the total number of open connections and files for the process(s) specified 
        by pid. The pid can be a list.
        """

        pid_string = ','.join(pid)
        out = subprocess.check_output(['lsof', '-nl', '-p', '%s'%pid_string]).decode('UTF-8')
        
        connections = 0
        files = 0

        for line in out.split('\n'):
            if 'TCP' in line or 'UDP' in line:
                connections+=1
            else: 
                files+=1

        return connections, files

    def plot_data(self):
        """Make a plot of the open connections and files vs time"""
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pylab as plt 
        matplotlib.style.use('fivethirtyeight')
        
        times = self.times
        data = self.data
        pid = self.pid

        plt.plot([time - times[0] for time in times], data['connections'], label='connections')
        plt.plot([time - times[0] for time in times], data['files'], label='files')
        plt.semilogy()
        plt.xlabel('time (s)')
        plt.ylabel('N open files')
        plt.legend(fontsize='small')
        plt.tight_layout()
        plt.savefig('{pid}.png'.format(pid=pid))

    def get_pids(self):
        """Helper function to get pids out of a file or turn the single pid into a string"""
        if self.file is None: 
            if type(pid) is not list: 
                pid = [str(self.pid)]
        else:
            with open(self.file) as f: 
                pid = [pid for pid in f.read().split('\n') if len(pid) > 0]
        return pid

    def start(self): 
        """Start the monitoring"""
        
        print(bc.BOLD + "Collecting data for pid %d -- press ctrl+c to exit"%self.pid + bc.ENDC)
        
        delay = self.delay
        
        while True: 
            time_in = time.time()

            pids = self.get_pids()
            
            try:
                connections, files = self.get_open_files(pids)
                self.data['connections'].append(connections)
                self.data['files'].append(files)
                self.times.append(time.time())

                if not self.quiet: 
                    print(time.time(), res)

                time_out = time.time()
                dtime = time_out-time_in

                if dtime < delay: 
                    time.sleep(delay-dtime)

            except subprocess.CalledProcessError: 
                print(bc.WARNING + "Process %d finished, doesn't exist, or doesn't have TCP connections"%self.pid + bc.ENDC)
                break

        self.plot_data()
            
    def signal_handler(self, signal, frame): 
        if not self.no_plot: 
            self.plot_data()
        sys.exit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Monitor open files for a process -- produces a plot upon exit')
    parser.add_argument('pid', type=int, help='pid of process to monitor')
    parser.add_argument('--no-plot', dest='no_plot', action='store_true', help='skip making the plot at the end')
    parser.add_argument('--quiet', dest='quiet', action='store_true', help='do not print timings to console')
    parser.add_argument('--delay', dest='delay', action='store', type=float, help='delay between measurements in seconds', default = 0.2)
    parser.add_argument('--file', dest='file', action='store', type=str, help='filename to use for reading a list of pids, one per line')

    args = parser.parse_args()

    fm = FilesMonitor(args.pid, args.no_plot, args.quiet, args.delay, args.file)
    fm.start()

