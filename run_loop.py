#!/usr/bin/python
import subprocess
import datetime

i = 0
cmd = "main.sh probe.conf 1"

while True:
    print "{0} run {1}:".format(datetime.datetime.now(), i),
    try:
        subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).wait()
        print ("ok")
    except:
        print ("failed")
    finally:
        i += 1

