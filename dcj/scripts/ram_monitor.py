#!/bin/env python
"""
ram_monitor.py
Python script for monitoring RAM usage

Input: filname with a pid
Display: RAM usage animation
Output: RAM usage log
"""
import sys,time,numpy as n
#from pylab import *

monfile = sys.argv[1]
logfile = monfile+'.log'
interval = 2 #seconds
range = 5 #minutes
length = int(5*60/interval)

kb_buffer = n.zeros(length)
i = 0
print "This is ram_monitor.py. CTRL-C to Exit"
print "Monitoring %s > %s"%(monfile,logfile)
open(logfile,'a').close()

waiting = False
while(True):
    pid = open(monfile).read().strip()
    try:
        status = open('/proc/%s/status'%pid)
        if waiting: print "valid pid found. Now monitoring: %s"%(pid)
        waiting=False
    except(IOError):
        if not waiting:
            print "stale pid. Waiting for update"
            waiting = True
    if not waiting:
        kb = int(status.read().split('VmSize:')[1].split()[0])
        ofile = open(logfile,'a')
        ofile.write("%f    %d\n"%(time.time(),kb))
        ofile.close()

    i = (i+1)%length
    time.sleep(interval)
    
