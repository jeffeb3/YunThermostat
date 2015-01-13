#!/bin/sh

cd /usr/local/bin/thermostat

echo Starting the Thermostat > /root/status.txt

./thermostatApp.py
