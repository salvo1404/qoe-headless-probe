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
from subprocess import Popen, PIPE

logging.config.fileConfig('logging.conf')


def launch_tstat_deamon(configuration):
	cmd = "./probe/runTstatLiveCapture probe/TstatLiveCapture.py start %s" % configuration
	FNULL = open(os.devnull, 'w')
	p = Popen(cmd, stdout=FNULL, stderr=FNULL, shell=True)
	
def stop_tstat_deamon(configuration):
	grep = Popen(['pgrep', 'tstat'], stdout=PIPE, stderr=PIPE)
	res = grep.communicate()
	cmd = "./probe/runTstatLiveCapture probe/TstatLiveCapture.py %s %s" %(res[0][0:-1],configuration)
	FNULL = open(os.devnull, 'w')	
	p = Popen(cmd, stdout=FNULL, stderr=FNULL, shell=True)  


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
    for i in range(nun_runs):      	
      	for url in open(pjs_config['urlfile']):	
		launch_tstat_deamon(conf_file)		
		stats = launcher._browse_url(url)
		if stats is None:
		    logger.warning('Problem in session %d.. skipping' % i)
		    continue
		if not os.path.exists(plugin_out_file):
		    logger.error('Plugin outfile missing.')
		    exit("Plugin outfile missing.")
		stop_tstat_deamon(conf_file)
		dbcli.load_to_db(stats)
		logger.debug('Ended browsing run n.%d' % i)	

		new_fn = backupdir + '/' + plugin_out_file.split('/')[-1] + '.run%d' % i
		shutil.copyfile(plugin_out_file, new_fn)	# Quick and dirty not to delete Tstat log
		open(plugin_out_file, 'w').close()
		new_har = backupdir + '/' + harfile.split('/')[-1] + '.run%d' % i
		os.rename(harfile, new_har)
		logger.debug('Saved plugin file for run n.%d: %s' % (i,new_fn))
	
		monitor = Monitor(config)
		monitor.run_active_measurement()
		logger.debug('Ended Active probing for run n.%d' % i)
		for tracefile in os.listdir('.'):
		    if tracefile.endswith('.traceroute'):
		        new_fn_trace = backupdir + '/' + tracefile + '.run%d' % i
		        os.rename(tracefile, new_fn_trace)

    jc = JSONClient(config)
    jc.prepare_and_send()
