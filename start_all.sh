#!/bin/sh
 
# Sample script to start all services
./data_collector.py
./wu_temp_collector.py -t 600
./radiothermostat_collector.py -t 300
./cosm_submit.py -t 600


