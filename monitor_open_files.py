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
    no_plot = False

    def __init__(self, pid, no_plot): 
        self.pid = pid
        self.no_plot = no_plot

        signal.signal(signal.SIGINT, self.signal_handler)

    @staticmethod
    def get_open_files(pid):
        pids = []
        out = subprocess.check_output(['lsof', '-nl', '-p', '%d'%pid]).decode('UTF-8')
        
        for line in out.split('\n'):
            try: 
                pids.append(int(re.findall('\w+\s+(\d+)', line)[0]))
            except IndexError: 
                pass
        return pids.count(pid)

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
        plt.savefig('{time}_{pid}.png'.format(time=times[0], pid=pid))

    def start(self): 
        print(bc.BOLD + "Collecting data -- press ctrl+c to exit" + bc.ENDC)
        while True: 
            time_in = time.time()
            res = self.get_open_files(self.pid)
            print(time.time(), res)
            self.times.append(time.time())
            self.data.append(res)

            time_out = time.time()
            dtime = time_out-time_in

            if dtime < 0.5: 
                time.sleep(0.5-dtime)

    def signal_handler(self, signal, frame): 
        if not self.no_plot: 
            self.plot_data()
        sys.exit(0)

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Monitor open files for a process -- produces a plot upon exit')
    parser.add_argument('pid', type=int, help='pid of process to monitor')
    parser.add_argument('--no-plot', dest='no_plot', action='store_true', help='skip making the plot at the end')
    args = parser.parse_args()

    fm = FilesMonitor(args.pid, args.no_plot)
    fm.start()

