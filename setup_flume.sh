#!/bin/bash
mkdir .toflume
FLUMEDIR=".toflume"

echo "Downloading Apache Flume ..."
wget http://mirrors.ircam.fr/pub/apache/flume/1.5.0/apache-flume-1.5.0-bin.tar.gz
tar -zxvf apache-flume-1.5.0-bin.tar.gz > /dev/null
echo "Configuring Apache Flume ..."

cat > apache-flume-1.5.0-bin/conf/flume-spool.conf <<EOL
## Describe/configure SpoolDirectory
agent.sources = SpoolDirectory
agent.sources.SpoolDirectory.type = spooldir
agent.sources.SpoolDirectory.spoolDir = $(pwd)/qoe-headless-probe/$FLUMEDIR
agent.sources.SpoolDirectory.fileHeader = true
agent.sources.SpoolDirectory.deletePolicy = immediate
agent.sources.SpoolDirectory.deserializer.maxLineLength = 100000000
# agent.sources.SpoolDirectory.deserializer.schemaType = LITERAL
# Granularity at which to batch transfer to the channel
# agent.sources.apache.batchSize = 100
agent.sources.SpoolDirectory.interceptors = itime ihost itype
# http://flume.apache.org/FlumeUserGuide.html#timestamp-interceptor
agent.sources.SpoolDirectory.interceptors.itime.type = timestamp
# http://flume.apache.org/FlumeUserGuide.html#host-interceptor
agent.sources.SpoolDirectory.interceptors.ihost.preserveExisting = true
agent.sources.SpoolDirectory.interceptors.ihost.type = host
agent.sources.SpoolDirectory.interceptors.ihost.useIP = true
agent.sources.SpoolDirectory.interceptors.ihost.hostHeader = host
# http://flume.apache.org/FlumeUserGuide.html#id-interceptor
agent.sources.SpoolDirectory.interceptors.iuserId.type = static
agent.sources.SpoolDirectory.interceptors.iuserId.key = userId
agent.sources.SpoolDirectory.interceptors.iuserId.value = wandboard@eurecom.fr
# http://flume.apache.org/FlumeUserGuide.html#static-interceptor
agent.sources.SpoolDirectory.interceptors.itype.type = static
agent.sources.SpoolDirectory.interceptors.itype.key = log_type
agent.sources.SpoolDirectory.interceptors.itype.value = probes_data

agent.sources.SpoolDirectory.channels = memoryChannel
agent.channels = memoryChannel
agent.channels.memoryChannel.type = memory
agent.channels.memoryChannel.capacity = 1000000
agent.channels.memoryChannel.transactionCapacity = 10000

## Send to Flume Collector on 1.2.3.4 (Hadoop Slave Node)
agent.sinks = AvroSink
agent.sinks.AvroSink.channel = memoryChannel
agent.sinks.AvroSink.type = avro
agent.sinks.AvroSink.hostname = 192.168.104.247
#agent.sinks.AvroSink.hostname = 192.168.45.48
agent.sinks.AvroSink.port = 10200
#agent.sinks.AvroSink.batch-size = 100

EOL

cd apache-flume-1.5.0-bin/conf/
mv flume-env.sh.template flume-env.sh
JAVAHOME=$(readlink -f /usr/bin/java | sed "s:bin/java::")
#echo $JAVAHOME   
JAVADIR="JAVA_HOME=$JAVAHOME"
sed -i "1 i $JAVADIR" flume-env.sh

cd ..
echo "Downloading Apache Flume libraries..."
rm -fR lib
wget http://firelog.eurecom.fr/mplane/software/flumelib.tar.gz
tar -zxvf flumelib.tar.gz > /dev/null
rm flumelib.tar.gz

echo "Starting flume Agent..."
bin/flume-ng agent --conf conf --conf-file conf/flume-spool.conf --name agent 

echo "Done."
