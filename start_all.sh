#!/bin/sh
 
# Sample script to start all services
nohup ./data_collector.py &
nohup ./wu_temp_collector.py -t 600 &
nohup ./radiothermostat_collector.py -t 300 &
nohup ./cosm_submit.py -t 600 &


