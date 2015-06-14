YunThermostat
=============

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/jeffeb3/YunThermostat?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)
[![Documentation Status](https://readthedocs.org/projects/yunthermostat/badge/?version=latest)](https://readthedocs.org/projects/yunthermostat/?badge=latest)

Real docs are [here](yunthermostat.rtfd.org/en/latest)

TODO:
=====
 - Update the docs
   - Make links to the online documentation from the web interface. For example, have a section on howto set up the
   weather API in the docs from the weather API settings section.
 - Weather test button
 - Graph history length buttons
 - Ability to add data points for Thingspeak away detection
 - watchdogs on the atmega and the arm with reboots.
  - Also add checks for running the heat/AC too long, or too frequently.
 - email alerts for resets/errors
  - Working for the SMTP handler. Need to add explicit events for starting (restarting) and OOR errors.
 - command line arguments
 - Error handling, especially:
   - imports
 - Check into the ATMEGA config for disabling the cool function.
 - ATMEGA Display:
  - Configure to show the time
  - Configure to show the outdoor temperature (possibly throught the bridge.py interface).
