#!/usr/bin/env python

## Update Python path to include libraries on SD card.
#import sys
#sys.path.append('/mnt/sda1/python-packages')

# Import system libraries.
import gevent
from gevent import monkey; monkey.patch_all() # this affects the other imports!
from gevent.queue import Queue
import socket
import time
import json
import urllib2
import os

# Import flask library.
from bottle import run, Bottle
from bottle import route, static_file, request, template, response

web = Bottle()

plotData = []

def formattedPlotData():
    ''' Format the global plotData object to be in the format that flot expects'''
    textData = ''
    textData += '[['
    for time, value in plotData:
        textData += '[ %f, %f],' % (time, value)
    textData += ']]'
    return textData

currentMeasurement = Queue(1)

def queryForever():
    '''Try to read from a REST server forever'''
    try:
        while True:
            # Get data from server.
            data = json.load(urllib2.urlopen("http://10.0.2.208/arduino/sensors"));
            data["time"] = (time.time() - time.timezone) * 1000.0
            # is accessing this object allowed without a lock?
            print 'new measurement:' + str(data)
            plotData.append((data["time"], data["temperature"]))
            try:
                currentMeasurement.get_nowait()
            except gevent.queue.Empty:
                True
            currentMeasurement.put_nowait(data)
            gevent.sleep(30)
            
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
            data = None
            try:
                data = currentMeasurement.get()
            except gevent.queue.Empty:
                pass


            print 'received:' + str(data)
            # Stop if the server closed the connection.
            if not data:
                raise StopIteration
            # Send the data to the web page in the server sent event format.
            eventText = ''
            eventText += 'data: {\n'
            eventText += 'data:   "time" : %f,\n' % data["time"]
            eventText += 'data:   "temperature" : %f,\n' % data["temperature"]
            eventText += 'data:   "humidity" : %f\n' % data["humidity"]
            eventText += 'data: }\n\n'
            #print eventText,
            yield eventText
            # Sleep so the CPU isn't consumed by this thread.
            time.sleep(1.0)
    except gevent.queue.Empty:
        # Error connecting to socket. Raise StopIteration to quit.
        raise StopIteration

@web.route('/')
def root():
    return template('index', plotData = formattedPlotData())

# router for the jquery scripts
@web.route('/javascript/<path:path>')
def JavascriptCallback(path):
  return static_file('javascript/'+path, root='.')

#@web.route('/javascript/<path:path>')
#def javascript(path):
#    print os.path.join('/usr/share/javascript',path)
#    return app.send_static_file(os.path.join('/usr/share/javascript',path))

if __name__ == '__main__':
    gevent.spawn(queryForever)
    web.run(host='0.0.0.0', debug=True, server='gevent')
    