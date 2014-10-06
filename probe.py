#!/usr/bin/python
import sys
import os
import shutil
import logging
import logging.config
from probe.Configuration import Configuration
from probe.PJSLauncher import PJSLauncher
from probe.DBClient import DBClient
from probe.ActiveMeasurement import Monitor
from probe.JSONClient import JSONClient
from probe.TstatLiveCapture import TstatLiveCapture
import time
import subprocess
import threading

logging.config.fileConfig('logging.conf')


class TstatDaemonThread(threading.Thread):

    def __init__(self, config, flag):
        self.flag = flag
        if self.flag == 'start':
            self.script = config.get_tstat_configuration()['start']
            self.tstatpath = os.path.join(config.get_tstat_configuration()['dir'], 'tstat/tstat')
            self.interface = config.get_tstat_configuration()['netinterface']
            self.netfile = config.get_tstat_configuration()['netfile']
            self.outdir = config.get_tstat_configuration()['tstatout']
            self.is_daemon = True
        else:
            self.script = config.get_tstat_configuration()['stop']
            self.is_daemon = False

        thread = threading.Thread(target=self.run, args=())
        thread.daemon = self.is_daemon
        logging.info("TstatDaemonThread running [%s] is_daemon = %s..." % (os.path.basename(self.script), str(self.is_daemon)))
        thread.start()

    def run(self):
        if self.flag == 'start':
            cmd = "%s %s %s %s %s" % (self.script, self.tstatpath, self.interface, self.netfile, self.outdir)
            p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).wait()
        else:
            p = subprocess.Popen(self.script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).wait()


#def launch_tstat_deamon(configuration):
#    script = configuration.get_tstat_configuration()['start']
#    tstatpath = os.path.join(configuration.get_tstat_configuration()['dir'], 'tstat/tstat')
#    interface = configuration.get_tstat_configuration()['netinterface']
#    netfile = configuration.get_tstat_configuration()['netfile']
#    outdir = configuration.get_tstat_configuration()['tstatout']
#    cmd = "%s %s %s %s %s" % (script, tstatpath, interface, netfile, outdir)
#    p = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=False).wait()
#    logger.info('Tstat is running...')


#def stop_tstat_deamon(configuration):
#    script = configuration.get_tstat_configuration()['stop']
#    p = subprocess.Popen(script, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True).wait()
#    logger.info('Tstat stopped.')


if __name__ == '__main__':
    if len(sys.argv) < 4:
        exit("Usage: %s %s %s %s" % (sys.argv[0], 'nr_runs', 'conf_file', 'backup folder'))
    nun_runs = int(sys.argv[1])
    conf_file = sys.argv[2]
    backupdir = sys.argv[3]
    logger = logging.getLogger('probe')
    config = Configuration(conf_file)        
    plugin_out_file = config.get_database_configuration()['tstatfile']
    harfile = config.get_database_configuration()['harfile']
    launcher = PJSLauncher(config)    
    
    logger.debug('Backup dir set at: %s' % backupdir)
    dbcli = DBClient(config)
    dbcli.create_tables()
    logger.debug('Starting nr_runs (%d)' % nun_runs)
    pjs_config = config.get_phantomjs_configuration()
    t = TstatDaemonThread(config, 'start')
    for i in range(nun_runs):
        for url in open(pjs_config['urlfile']):
            print('url = ', url)

            #launch_tstat_deamon(config)
            #launch_tstat_deamon(conf_file)
            stats = launcher._browse_url(url)
            if stats is None:
                logger.warning('Problem in session %d.. skipping' % i)
                continue
            if not os.path.exists(plugin_out_file):
                logger.error('Plugin outfile missing.')
                exit("Plugin outfile missing.")


            #stop_tstat_deamon(conf_file)
            dbcli.load_to_db(stats)
            print ('loaded stats')
            logger.debug('Ended browsing run n.%d' % i)

            new_fn = backupdir + '/' + plugin_out_file.split('/')[-1] + '.run%d' % i
            shutil.copyfile(plugin_out_file, new_fn)	# Quick and dirty not to delete Tstat log
            open(plugin_out_file, 'w').close()
            new_har = backupdir + '/' + harfile.split('/')[-1] + '.run%d' % i
            os.rename(harfile, new_har)
            logger.debug('Saved plugin file for run n.%d: %s' % (i, new_fn))
            monitor = Monitor(config)
            monitor.run_active_measurement()
            logger.debug('Ended Active probing for run n.%d' % i)
            for tracefile in os.listdir('.'):
                if tracefile.endswith('.traceroute'):
                    new_fn_trace = backupdir + '/' + tracefile + '.run%d' % i
                    os.rename(tracefile, new_fn_trace)

    s = TstatDaemonThread(config, 'stop')
    print 'Ended...'
    jc = JSONClient(config)
    jc.prepare_and_send()
