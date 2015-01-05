YunThermostat
=============

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/jeffeb3/YunThermostat?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Developing a thermosatat running on the Arduino Yun

arduino_setup.txt has instructions for setting up the Arduino Yun.

thermostat.ino is the sketch that gets loaded onto the Atmega side of the Arduino Yun

linux contains the script that will run on the OpenWRT or Linux side of the Arduino Yun.

linux/Thermostat.py is the main python function that queries the atmega side, and provides a web interface.

linux/views is the folder with web templates for the python web interface.

linux/javascript is a link to the javascript libraries stored on this machine. (/usr/share/javascipt).
