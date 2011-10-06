#!/usr/bin/python -O

'''
This file is an attempt to check the hosts on the network are valid
'''

import os
import signal
from subprocess import Popen, PIPE

import labmap

wd = os.path.dirname(__file__)
with open(os.path.join(wd, 'data', 'hosts')) as f:
    locator = labmap.Locator(f)

    for lab in locator.getLabs():
        for host, location in locator.getMap(lab):

            class Alarm(Exception):
                pass

            def alarmHandler(signum, frame):
                raise Alarm

            signal.signal(signal.SIGALRM, alarmHandler)
            signal.alarm(5)
            terminated = False
            try:
                proc = Popen(["ssh", host], stdout=PIPE, stderr=PIPE)
                stdout, stderr = proc.communicate()
                signal.alarm(0)
            except Alarm:
                terminated = True
                proc.terminate()

            #We assume this is just asking for password if it is terminated
            if terminated == False and  'Name or service not known' in stderr:
                print 'Lookup of %s failed' % host
            else:
                print 'Fine for %s' % host
