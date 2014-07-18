#!/bin/bash
#title           :setup.sh
#description     :Installation and configuration script for the mPlane headless QoE probe.
#author          :marco.milanesio@eurecom.fr
#date            :20140716
#version         :0.1    
#usage           :bash setup.sh [--flume]
#bash_version    :4.2.45(1)-release
#==========================================================================================
flumeflag=1
if [[ "$1" == "-h" || "$1" == "--help" ]]; then
  echo "Usage: `basename $0` [--flume]"
  exit 0
fi
if [ -n "$1" ]; then
    if [ "$1" == "--flume" ]; then
        flumeflag=0
        echo "Flag set for flume agent."
    fi
fi

#######################
if [ $flumeflag -eq 0 ]; then
    MODE=3
else
    MODE=1
fi
#######################

echo -n "Postgresql admin user name:"
read dbadmin
DBNAME='testingmplane'
DBUSER='testingmplane'

echo 'Checking Postgresql installation ...'
type psql >/dev/null 2>&1 || { echo >&2 "Psql required but not installed.  Aborting."; exit 1; }
echo -n 'Creating database ... '
if psql -lqt | cut -d\| -f 1 | grep -w $DBNAME > /dev/null; then
   echo "Warning: DB already existing ..."
else
   psql -U $dbadmin -c "CREATE DATABASE $DBNAME" > /dev/null
   echo "done."
fi

echo -n "Creating role $DBUSER ... "
psql -U $dbadmin -c "CREATE ROLE $DBUSER WITH LOGIN" > /dev/null
psql -U $dbadmin -c "GRANT ALL PRIVILEGES ON DATABASE $DBNAME to $DBUSER" > /dev/null
echo "done."
echo -n "Checking python version ... "
if python -c 'import sys; sys.exit(1 if sys.hexversion<0x03000000 else 0)'
then
    echo "Python3 detected. Aborting ..."
    exit 1
else
    echo "Python2 detected."
fi


#if [ $MODE -eq 3 ]; then
#    mkdir .toflume
#    echo "Downloading Apache Flume ..."
#    wget http://www.apache.org/dyn/closer.cgi/flume/1.5.0/apache-flume-1.5.0-bin.tar.gz
#    tar xvf apache-flume-1.5.0-bin.tar.gz
    
    
echo "Downloading Modified Tstat ..."
wget http://firelog.eurecom.fr/mplane/software/eur-tstat-2.4.tar.gz
tar -xzf eur-tstat-2.4.tar.gz > /dev/null
echo "Building ..."
TSTATDIR="eur-tstat-2.4"
cd $TSTATDIR
./autogen.sh 
./configure 
make
cd ..
echo "Done."

ARCH=$(uname -m)
echo "Downloading phantomjs ..."
DIR="phantomjs-1.9.7-linux-$ARCH"
NAME="$DIR.tar.bz2"
DLINK="https://bitbucket.org/ariya/phantomjs/downloads/$NAME"
wget $DLINK
echo "Unpacking ..."
tar xvf $NAME


echo "Downloading qoe-headless-probe ..."
wget http://firelog.eurecom.fr/mplane/software/qoe-headless-probe.tar.gz
tar -xzf qoe-headless-probe.tar.gz > /dev/null
echo "Configuring ..."
PROBEDIR=$(pwd)/qoe-headless-probe
cd $PROBEDIR
sudo gcc -o probe/runTstatLiveCapture probe/runTstatLiveCapture.c
sudo chmod 4755 probe/runTstatLiveCapture
cd ..
echo "Done."

echo "Writing configuration file"

cat > $PROBEDIR/probe.conf <<EOL
[phantomjs]
dir=$(pwd)/$DIR
profile=none
script=$(pwd)/qoe-headless-probe/netsniff_SB_v1.6.js
urlfile=$(pwd)/qoe-headless-probe/url.list
logfile=$(pwd)/qoe-headless-probe/probe/pjs.log
thread_timeout=180
thread_outfile=$(pwd)/qoe-headless-probe/probe/thread_out.file
thread_errfile=$(pwd)/qoe-headless-probe/probe/thread_err.file

[tstat]
dir=$(pwd)/$TSTATDIR
netfile=$(pwd)/$TSTATDIR/tstat-conf/mplane.conf
tstatout=/tmp
netinterface=eth0
logfile=$(pwd)/qoe-headless-probe/probe/tstat.log

[database]
dbhost=localhost
dbname=$DBNAME
dbuser=$DBUSER
rawtable=plugin_raw
activetable=active
pluginoutfile=/tmp/plugin_test.out
tstatfile=/tmp/tstat.out/log_own_complete
harfile=/tmp/phantomjs.har

[server]
mode=$MODE
ip=193.55.113.252
port=13373

EOL

echo "Done. Please check the probe.conf file before proceeding."
echo "Probe ready: fill $PROBEDIR/url.list with websites."
exit 0

