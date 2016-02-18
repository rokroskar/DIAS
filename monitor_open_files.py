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
    pid = None
    times = []
    data = []

    def __init__(self, pid, no_plot, quiet, delay, file = None): 
        self.pid = pid
        self.no_plot = no_plot
        self.quiet = quiet
        self.delay = delay
        self.file = file

        signal.signal(signal.SIGINT, self.signal_handler)

    @staticmethod
    def get_open_files(pid):
        pid_string = ','.join(pid)
        out = subprocess.check_output(['lsof', '-nl', '-p', '%s'%pid_string]).decode('UTF-8')
        
        connections = 0
        for line in out.split('\n'):
            if 'TCP' in line:
                connections+=1

        return connections

    def plot_data(self):
        """Make a plot of the files vs time"""
        import matplotlib
        matplotlib.use('agg')
        import matplotlib.pylab as plt 
        matplotlib.style.use('fivethirtyeight')
        
        times = self.times
        data = self.data
        pid = self.pid

        plt.plot([time - times[0] for time in times], data, 'o')
        plt.xlabel('time (s)')
        plt.ylabel('N open files')
        plt.tight_layout()
        plt.savefig('{pid}.png'.format(pid=pid))

    def start(self): 
        print(bc.BOLD + "Collecting data for pid %d -- press ctrl+c to exit"%self.pid + bc.ENDC)
        
        delay = self.delay
        
        pid = self.pid

        if self.file is None: 
            if type(pid) is not list: 
                pid = [str(self.pid)]
        else:
            with open(self.file) as f: 
                pid = [pid for pid in f.read().split('\n') if len(pid) > 0]
        
        while True: 
            time_in = time.time()
            try:
                res = self.get_open_files(pid)
                if not self.quiet: 
                    print(time.time(), res)

                self.times.append(time.time())
                self.data.append(res)

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

