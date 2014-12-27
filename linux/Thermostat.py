#!/usr/bin/env python

# todo:
# X Install on Yun
#  X Switch from gevents to threading...
# X Add uptime on atmega
# X style sheet (or just use mobile)
# X Add humidity, and heat on to front page.
# X Add time to front page
# - Create file history of status/temps (csv?, shelf?)
# - Add ways to navigate the graph
# - watchdogs on the atmega and the arm with reboots
# - email alerts for resets/errors
# - hourly program format
# - hourly program interface (jquery)
# - smart (ping) adjustments
# - GPS fencing

# Import system libraries.
import threading
import time
import json
import urllib2
import os
import copy

# Import flask library.
from bottle import run, Bottle, PasteServer
from bottle import route, static_file, template, response

web = Bottle()

# Shared data and locks
plotData = []
plotDataLock = threading.RLock()
currentMeasurement = None
currentMeasurementLock = threading.RLock()

def uptime():
    ''' get this system's seconds since starting '''    
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

class QueryThread(threading.Thread):
    ''' This thread runs continuously regarless of the interaction with the user.'''

    def __init__(self):
        threading.Thread.__init__(self)
        self.quit = False # set to True when you want to stop the while loop.
        self.lastMeasurementTime = 0
        self.hysteresisDegreesF = 0.3
    
    def run(self):
        '''Try to read from the arduino forever'''
        while not self.quit:
            self.lastMeasurementTime = time.time()

            # Get data from server.
            data = json.load(urllib2.urlopen("http://10.0.2.208/arduino/sensors"));
            data["time"] = (time.time() - time.timezone) * 1000.0
            data["py_uptime_ms"] = uptime() * 1000.0
            with plotDataLock:
                plotData.append(data)

            with currentMeasurementLock:
                global currentMeasurement
                currentMeasurement = data

            # Calculate what the set point should be
            setPoint = 71.0 # degrees F
            if (data["temperature"] < setPoint - self.hysteresisDegreesF):
                # we are more than the allowable amount below our set point
                
                # Turn the heat on!
                urllib2.urlopen("http://10.0.2.208/arduino/heat/1")

            elif (data["temperature"] > setPoint + self.hysteresisDegreesF):
                # we are more than the allowable temperature above our set point
                
                # Turn off the heat!
                urllib2.urlopen("http://10.0.2.208/arduino/heat/0")

            # sleep a moment at a time, so that we can catch the quit signal
            while (time.time() - self.lastMeasurementTime) < 30.0 and not self.quit:
                time.sleep(0.5)
    
    def stop(self):
        self.quit = True

@web.route('/measurements')
def yunserver_sse():
    '''  Generator function to connect to the YunServer instance and send
         all data received from it to the webpage as HTML5 server sent events. '''

    # Convert the response to an event stream.
    response.content_type = 'text/event-stream'

    while True:

        # Get data from thead.
        data = None
        with currentMeasurementLock:
            # deep copy
            data = copy.copy(currentMeasurement)

        # Stop if the thread stopped.
        if not data:
            raise StopIteration

        # Send the data to the web page in the server sent event format.
        yield 'data: %s\n\n' % json.dumps(data)

        # Sleep so the CPU isn't consumed by this thread. This will determine the update rate of the SSE.
        time.sleep(0.5)

@web.route('/')
def root():
    ''' Return the template, with the formatted data where the {{}} braces are.'''

    # store this information in key-value pairs so that the template engine can find them.
    webPageInformation = \
    {
        "tempPlotData" : '',
        "humidPlotData" : '',
        "heatPlotData" : '',
        "arduinoUptimePlotData" : '',
        "linuxUptimePlotData" : '',
    }
    
    with plotDataLock:
        #plotData = plotdData[-1000:] TODO
        for data in plotData[-1000:]: # clip to 1000 points, that should be enough for now
            webPageInformation['tempPlotData']          += '[ %f, %f],' % (data["time"], data["temperature"])
            webPageInformation['humidPlotData']         += '[ %f, %f],' % (data["time"], data["humidity"])
            webPageInformation['heatPlotData']          += '[ %f, %d],' % (data["time"], data["heat"])
            webPageInformation['arduinoUptimePlotData'] += '[ %f, %f],' % (data["time"], data["uptime_ms"])
            webPageInformation['linuxUptimePlotData']   += '[ %f, %f],' % (data["time"], data["py_uptime_ms"])

    # Add the outside brackets to each plot data.
    for key, value in webPageInformation.items():
        webPageInformation[key] = '[' + value + ']'

    webPageInformation["ipaddress"] = os.uname()[1]
    webPageInformation["timezone"] = time.timezone * 1000.0

    # replace parts of views/index.tpl with the information in the webPageInformation dictionary.
    return template('index', **webPageInformation)

# router for the jquery scripts
@web.route('/javascript/<path:path>')
def JavascriptCallback(path):
    ''' Just return any files in the javascript folder. '''
    return static_file('javascript/'+path, root='.')

if __name__ == '__main__':
    # create an instance of the query.
    query = QueryThread()
    
    # start the thread.
    query.start()
    
    # start the web server
    web.run(host='0.0.0.0', debug=True, server=PasteServer)
    
    # when the server stops, call quit on the thread.
    query.stop()
