YunThermostat
=============

[![Gitter](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/jeffeb3/YunThermostat?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge)

Developing a thermosatat running on the Arduino Yun

Unfortunately, I just reogranized everything, and I'm not up to date on the docs, so I'm going to just leave this blank for now.

TODO:
=====
 - Update the docs
   - Explore using another webpage, such as ReadTheDocs to do my documentation.
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

