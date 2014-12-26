#!/usr/bin/env python

# todo:
# X Install on Yun
#  X Switch from gevents to threading...
# X Add uptime on atmega
# - Create file history of status/temps
# - watchdogs on the atmega and reboots of the arm
# - email alerts for resets
# - hourly program format
# X style sheet (or just use mobile)
# - Add time to front page
# X Add humidity, and heat on to front page.
# - hourly program interface (jquery)
# - smart (ping) adjustments
# - GPS fencing

# Import system libraries.
import threading
import socket
import signal
import time
import json
import urllib2
import os
import copy

# Import flask library.
from bottle import run, Bottle, PasteServer
from bottle import route, static_file, request, template, response


web = Bottle()

plotData = []
plotDataLock = threading.RLock()

def ipaddress():
    # total hack, and will only work on Jeff's network
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("10.0.2.1",80))
    ip = str(s.getsockname()[0])
    s.close()
    return ip

def formattedPlotData():
    ''' Format the global plotData object to be in the format that flot expects'''
    temperatureData = ''
    temperatureData += '['
    humidityData = ''
    humidityData += '['
    with plotDataLock:
        for data in plotData:
            temperatureData += '[ %f, %f],' % (data["time"], data["temperature"])
            humidityData += '[ %f, %f],' % (data["time"], data["humidity"])
    temperatureData += ']'
    humidityData += ']'

    return { "tempPlotData" : temperatureData, "humidPlotData" : humidityData, "ipaddress" : ipaddress() }

currentMeasurement = None
currentMeasurementLock = threading.RLock()

def uptime():
    ''' get this system's seconds since starting '''    
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

class QueryThread(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.quit = False
    
    def run(self):
        '''Try to read from a REST server forever'''
        try:
            while not self.quit:
                lastMeasurementTime = time.time()
                # Get data from server.
                data = json.load(urllib2.urlopen("http://10.0.2.208/arduino/sensors"));
                data["time"] = (time.time() - time.timezone) * 1000.0
                data["py_uptime_ms"] = uptime() * 1000.0
                with plotDataLock:
                    plotData.append(data)
    
                with currentMeasurementLock:
                    global currentMeasurement
                    currentMeasurement = data
                
                # sleep a moment at a time, so that we can catch the quit signal
                while (time.time() - lastMeasurementTime) < 30.0 and not self.quit:
                    time.sleep(0.5)
                
        except socket.error: # todo, pick a better exception
            raise StopIteration
    
    def stop(self):
        self.quit = True

# Generator function to connect to the YunServer instance and send
# all data received from it to the webpage as HTML5 server sent events.
@web.route('/measurements')
def yunserver_sse():
    # Convert the response to an event stream.
    response.content_type = 'text/event-stream'

    try:
        while True:
            # Get data from thead.
            data = None
            with currentMeasurementLock:
                # deep copy
                data = copy.copy(currentMeasurement)

            # Stop if the server closed the connection.
            if not data:
                raise StopIteration

            # Send the data to the web page in the server sent event format.
            yield 'data: %s\n\n' % json.dumps(data)

            # Sleep so the CPU isn't consumed by this thread.
            time.sleep(0.5)
    except:
        # Error connecting to socket. Raise StopIteration to quit.
        raise StopIteration

@web.route('/')
def root():
    return template('index', **formattedPlotData())

# router for the jquery scripts
@web.route('/javascript/<path:path>')
def JavascriptCallback(path):
  return static_file('javascript/'+path, root='.')

if __name__ == '__main__':
    query = QueryThread()
    query.start()
    web.run(host='0.0.0.0', debug=True, server=PasteServer)
    query.stop()
