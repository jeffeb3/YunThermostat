#!/usr/bin/env python

# Import system libraries.
import datetime
import logging
import logging.handlers
import sys

# local imports
from thermostat import settings, web, Thermostat, sseLogHandler

# set up the logger
log = logging.getLogger()

# set up a way to record unhandled exceptions.
def log_uncaught_exceptions(*exc_info): 
    log.critical('Unhandled exception:', exc_info=exc_info)

# make the system log the final exception
sys.excepthook = log_uncaught_exceptions

if __name__ == '__main__':
    # logger setup
    formatter = logging.Formatter("%(asctime)s - %(message)s", 
                                  '%a, %d %b %Y %H:%M:%S')
    # log to a set of files.
    fileHandler = logging.handlers.RotatingFileHandler('./thermostatApp.log', maxBytes=10 * 1000 * 1000, backupCount=5, delay=True)
    fileHandler.setFormatter(formatter)
    log.addHandler(fileHandler)
    print '\n\nLogging to /var/log/thermostatApp.log\n\n'

    # and to the console
    stdoutHandler = logging.StreamHandler(sys.stdout)
    log.addHandler(stdoutHandler)
    
    # and to the web page.
    sseHandler = sseLogHandler.SseLogHandler(queueMaxSize = 25)
    sseFormat = '<tr>'
    sseFormat += '<th class="logLevel%(levelname)s ui-table-priority-3" style="color:red">%(levelname)s</th>'
    sseFormat += '<td class="logMessage ui-table-priority-1">%(message)s</td>'
    sseFormat += '<td class="logTime ui-table-priority-5">%(asctime)s</td>'
    sseFormat += '<td class="logName ui-table-priority-5">%(name)s</td>'
    sseFormat += '<td class="logFile ui-table-priority-5">%(filename)s:%(lineno)d</td>'
    sseFormat += '</tr>'
    sseHandler.setFormatter(logging.Formatter(sseFormat))
    log.addHandler(sseHandler)

    log.setLevel(logging.INFO)
    log.info('Started at %s', str(datetime.datetime.now()))
    
    settings.Load('settings.json')
    settings.FillEmptiesWithDefaults()
    settings.Save('settings.json')

    # create a Thermostat
    t = Thermostat.Thermostat()

    # start the thread
    t.start()
    
    # start the web server
    w = web.Web(t)
    w.web.route('/logs','GET',sseHandler.logs)
    w.web.route('/log_view','GET',sseLogHandler.SseLogHandler.log_view)
    w.run()

    log.critical("Exiting, but I'm supposed to live forever")
