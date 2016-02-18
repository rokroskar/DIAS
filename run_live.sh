#!/bin/bash

nodes=20
runtime=300
folder=dump/live_${nodes}nodes_${runtime}s/

#args= folder, ID, Port (port0=auto)
rm -r $folder
mkdir -p $folder
java -Dcom.sun.management.jmxremote.authenticate=false -Dcom.sun.management.jmxremote.ssl=false -Dcom.sun.management.jmxremote -Dcom.sun.management.jmxremote.port=8004 -Dvar=$(basename $folder)_0 -cp ./lib/*:./build/classes/ protocols.DIASLiveExperiment $folder 0 5555 & export APP_ID=$!
echo $APP_ID
./monitor_open_files.py $APP_ID --quiet &
sleep 1

i=1
while [ $i -lt $nodes ]; do
    java -Dvar=$(basename $folder)_$i -cp ./lib/*:./build/classes/ protocols.DIASLiveExperiment $folder $i 0 & export APP_ID=$!
    ./monitor_open_files.py $APP_ID --quiet &
    i=$((i+1))
done      
sleep 3

echo LETTING IT RUN FOR $runtime SECONDS
for i in $(seq $runtime 1);
do 
	echo $i
	sleep 1
done

echo ENDING
pkill java
sleep 1s

java -cp ./lib/*:./build/classes/ protocols.DIASLogReplayer $folder | tail -n+4 > summaries/$(basename $folder).dat 
#python plot.py summaries/$(basename $folder).dat
