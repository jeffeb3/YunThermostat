#!/usr/bin/env python

# todo:
# - Install on Yun
# - Add uptime on atmega
# - Create file history of status/temps
# - watchdogs on the atmega and reboots of the arm
# - email alerts for resets
# - hourly program format
# - style sheet (or just use mobile)
# - Add time to front page
# - Add humidity, and heat on to front page.
# - hourly program interface (jquery)
# - smart (ping) adjustments
# - GPS fencing

# Import system libraries.
import gevent
from gevent import monkey; monkey.patch_all() # this affects the other imports!
from gevent.event import AsyncResult
from gevent.lock import BoundedSemaphore
import socket
import signal
import time
import json
import urllib2
import os

# Import flask library.
from bottle import run, Bottle
from bottle import route, static_file, request, template, response

web = Bottle()

plotData = []
plotDataLock = BoundedSemaphore()

def formattedPlotData():
    ''' Format the global plotData object to be in the format that flot expects'''
    textData = ''
    textData += '[['
    with plotDataLock:
        for time, value in plotData:
            textData += '[ %f, %f],' % (time, value)
    textData += ']]'
    return textData

currentMeasurement = AsyncResult()

def uptime():
    ''' get this system's seconds since starting '''    
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

def queryForever():
    '''Try to read from a REST server forever'''
    try:
        while True:
            lastMeasurementTime = time.time()
            # Get data from server.
            data = json.load(urllib2.urlopen("http://10.0.2.208/arduino/sensors"));
            data["time"] = (time.time() - time.timezone) * 1000.0
            data["py_uptime"] = uptime()
            #print 'new measurement:' + str(data)
            with plotDataLock:
                plotData.append((data["time"], data["temperature"]))

            currentMeasurement.set(data)
            gevent.sleep(30 - (time.time() - lastMeasurementTime))
            
    except socket.error: # todo, pick a better exception
        raise StopIteration

# Generator function to connect to the YunServer instance and send
# all data received from it to the webpage as HTML5 server sent events.
@web.route('/measurements')
def yunserver_sse():
    # Convert the response to an event stream.
    response.content_type = 'text/event-stream'

    try:
        while True:
            # Get data from thead.
            data = currentMeasurement.get()

            # Stop if the server closed the connection.
            if not data:
                raise StopIteration
            # Send the data to the web page in the server sent event format. TODO use the JSON printer.
            eventText = ''
            eventText += 'data: {\n'
            eventText += 'data:   "time" : %f,\n' % data["time"]
            eventText += 'data:   "temperature" : %f,\n' % data["temperature"]
            eventText += 'data:   "humidity" : %f\n' % data["humidity"]
            eventText += 'data: }\n\n'
            #print eventText,
            yield eventText
            # Sleep so the CPU isn't consumed by this thread.
            time.sleep(0.5)
    except:
        # Error connecting to socket. Raise StopIteration to quit.
        raise StopIteration

@web.route('/')
def root():
    return template('index', plotData = formattedPlotData())

# router for the jquery scripts
@web.route('/javascript/<path:path>')
def JavascriptCallback(path):
  return static_file('javascript/'+path, root='.')

if __name__ == '__main__':
    gevent.signal(signal.SIGQUIT, gevent.kill)
    gevent.spawn(queryForever)
    web.run(host='0.0.0.0', debug=True, server='gevent')
