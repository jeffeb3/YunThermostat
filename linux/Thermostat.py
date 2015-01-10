#!/usr/bin/env python

# todo:
# X Install on Yun
#  X Switch from gevents to threading...
# X Add uptime on atmega
# X style sheet (or just use mobile)
# X Add humidity, and heat on to front page.
# X Add time to front page

# X hourly program format
# X hourly program interface (jquery)

# - Weather test button
# - Create file history of status/temps (csv?, shelf?)
# - Organize the Thermostat.py code.
# - Add ways to navigate the graph
# - watchdogs on the atmega and the arm with reboots
# - email alerts for resets/errors
# - command line arguments
# - Error handling, especially:
#   - imports
#   - urls
#   - settings
# - smart (ping) adjustments
# ? dropbox integration.
# - GPS fencing

# Import system libraries.
import threading
import time
import datetime
import json
import urllib2
import os
import sys
import copy
import commands
import shelve
import socket
import logging
import logging.handlers
import sseLogHandler
from smtplib import SMTPAuthenticationError, SMTPResponseException, SMTPRecipientsRefused

# set up the logger
log = logging.getLogger('Thermostat')
# common formatter
formatter = logging.Formatter("%(asctime)s - %(message)s", 
                              '%a, %d %b %Y %H:%M:%S')
# also log to a set of files.
fileHandler = logging.handlers.RotatingFileHandler('/var/log/thermostat.log', maxBytes=10000, backupCount=5, delay=True)
fileHandler.setFormatter(formatter)
log.addHandler(fileHandler)
print '\n\nLogging to /var/log/thermostat.log\n\n'
## and to the console
stdoutHandler = logging.StreamHandler(sys.stdout)
log.addHandler(stdoutHandler)
log.setLevel(logging.DEBUG)

# set up a way to record unhandled exceptions.
def log_uncaught_exceptions(*exc_info): 
    log.critical('Unhandled exception:', exc_info=exc_info)

# make the system log the final exception
sys.excepthook = log_uncaught_exceptions

# Import bottle library.
from bottle import run, Bottle, PasteServer
from bottle import route, static_file, template, response, request

# Import our email utility function
from email_utils import sendemail

web = Bottle()
sseHandler = sseLogHandler.SseLogHandler(web)
sseHandler.setFormatter(formatter)
log.addHandler(sseHandler)

days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

# Shared data and locks
plotData = []
plotDataLock = threading.RLock()
currentMeasurement = None
currentMeasurementLock = threading.RLock()

settings = {}
try:
    with open('settings.json', 'r') as fp:
        settings = json.load(fp)
        log.info('Loaded settings:')
        # this logs my password to the webpage... Dont do that.
        # log.info(json.dumps(settings, sort_keys=True, indent=4))
except:
    log.error('Failure to load settings. Setting to defaults')
    
    # These are the initial settings for the configuration page.
    settings = {}
    settings["doHeat"] = True
    settings["doCool"] = True

    settings["heatTempComfortable"] = 68.0
    settings["heatTempSleeping"] = 62.0
    settings["heatTempAway"] = 62.0

    settings["coolTempComfortable"] = 76.0
    settings["coolTempSleeping"] = 72.0
    settings["coolTempAway"] = 78.0

    settings["doEmail"] = True
    settings["smtp"] = 'smtp.gmail.com:587'
    settings["email_from"] = ''
    settings["email_to"] = ''
    settings["email_passw"] = ''
    settings["email_restart"] = True
    settings["email_oor"] = True

    for day in days:
        settings[day + "Night"] = 1320
        settings[day + "Morn"] = 360
    
    settings["apiKey"] = ''
    settings["weather_state"] = 'CO'
    settings["weather_city"] = 'Denver'
    
    # secret settings (not on the web page).
    settings["arduino_addr"] = "localhost"
    
    with open('settings.json', 'w') as fp:
        json.dump(settings, fp, sort_keys=True, indent=4)
    
settingsLock = threading.RLock()

def uptime():
    ''' get this system's seconds since starting '''    
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

def isPinging(host, max_tries = 10):
    for i in range(max_tries):
        command = 'ping -c 1 -w 1 -W 1 ' + host
        (rv, text) = commands.getstatusoutput(command)
        if rv == 0: # zero means response
            return True
    return False

class QueryThread(threading.Thread):
    ''' This thread runs continuously regarless of the interaction with the user.'''

    def __init__(self):
        threading.Thread.__init__(self)
        self.daemon = True
        self.quit = False # set to True when you want to stop the while loop.
        self.lastMeasurementTime = 0
        self.lastOutsideMeasurementTime = 0
        self.outsideTemp = 0
        self.sleeping = False
        self.away = False
    
    def run(self):
        '''Try to read from the arduino forever'''
        while not self.quit:
            # this try...except block is to log all exceptions. It's in this while loop because I want to keep going.
            try:
                self.lastMeasurementTime = time.time()
    
                # Gather data from Wunderground, but only every 10 minutes (limited for free api account)
                outsideTempUpdated = False
                if ((time.time() - self.lastOutsideMeasurementTime) > 360):
                    try:
                        apiKey = ""
                        weather_loc = ""
                        with settingsLock:
                            apiKey = settings["apiKey"]
                            weather_loc = settings["weather_state"] + '/' + settings["weather_city"]
                        outsideData = json.load(urllib2.urlopen("http://api.wunderground.com/api/" + apiKey + "/conditions/q/" + weather_loc + ".json"))
                        self.outsideTemp = outsideData['current_observation']['temp_f']
                        log.info('Retrieved outside temp:' + str(self.outsideTemp))
                        outsideTempUpdated = True
                        self.lastOutsideMeasurementTime = time.time()
                    except Exception as e:
                        # swallow any exceptions, we don't want the thermostat to break if there is no Internet
                        log.exception(e)
                        pass
    
                arduino_addr = ''
                with settingsLock:
                    arduino_addr = settings["arduino_addr"]
                
                # ping the server
                heartbeat = json.load(urllib2.urlopen("http://" + arduino_addr + "/arduino/heartbeat"));
    
                # Get data from server.
                data = json.load(urllib2.urlopen("http://" + arduino_addr + "/data/get/"));
                data = data["value"]
                data["time"] = time.time() * 1000.0
                data["py_uptime_ms"] = uptime() * 1000.0
                data["flappy_ping"] = False #isPinging("10.0.2.219")
                data["phone_ping"] = False #isPinging("10.0.2.222")
                data["outside_temp"] = self.outsideTemp
                data["outside_temp_updated"] = outsideTempUpdated
                data["sleeping"] = self.sleeping
                data["away"] = self.away
                
                # convert some things to float
                data["temperature"] = float(data["temperature"])
                data["humidity"] = float(data["humidity"])
                data["uptime_ms"] = float(data["uptime_ms"])
                data["heatSetPoint"] = float(data["heatSetPoint"])
                data["coolSetPoint"] = float(data["coolSetPoint"])
                data["lastUpdateTime"] = float(data["lastUpdateTime"])
                data["heat"] = int(data["heat"])
                data["cool"] = int(data["cool"])
                
                data["uptime_ms"] = heartbeat["uptime_ms"]
                
                log.info('Arduino (%.1fs) -- T: %.1f H: %.1f', data["lastUpdateTime"] / 1000.0, data["temperature"], data["humidity"])
    
                with plotDataLock:
                    global plotData
                    plotData.append(data)
                    plotData = plotData[-2880:] # clip to 24 hours
    
                with currentMeasurementLock:
                    global currentMeasurement
                    currentMeasurement = data
    
                # Calculate what the set point should be
                setRange = self.getSetTemperatureRange()
                
                # send the set point to the arduino
                urllib2.urlopen("http://" + arduino_addr + "/arduino/command/" + str(setRange[0]) + "/" + str(setRange[1]))
    
                # sleep a moment at a time, so that we can catch the quit signal
                while (time.time() - self.lastMeasurementTime) < 30.0 and not self.quit:
                    time.sleep(0.5)
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                log_uncaught_exceptions(*sys.exc_info())
                time.sleep(60.0) # sleep for extra long.
                continue

    
    def getSetTemperatureRange(self):
        now = datetime.datetime.now()
        day = days[(now.weekday() + 1) % 7] # python says 0 is Monday.
        wakeUp = None
        sleep = None
        with settingsLock:
            wakeUp = settings[day + 'Morn']
            sleep = settings[day + 'Night']
        
        minutes = now.minute + 60*now.hour
        if minutes < wakeUp:
            # we are still asleep
            self.sleeping = True
        elif minutes < sleep:
            # we are just waking up
            self.sleeping = False
        else:
            # we went back to sleep
            self.sleeping = True
        
        with settingsLock:
            if self.sleeping:
                return (settings["heatTempSleeping"], settings["coolTempSleeping"])
            else:
                return (settings["heatTempComfortable"], settings["coolTempComfortable"])

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

@web.route('/data.json')
def daq():
    '''  Respond with a single json object, the most recent data. '''

    # Get data from thead.
    data = None
    with currentMeasurementLock:
        # deep copy
        data = copy.copy(currentMeasurement)

    # Send the data to the web page in the server sent event format.
    return json.dumps(data, indent=4)

@web.route('/settings')
def settings_get():
    '''  Generator function to send updates of the settings to the web page. '''

    settings_copy = {}
    with settingsLock:
        settings_copy = copy.copy(settings)
    
    # Don't send the password out. We have enough security problems...
    del settings_copy["email_passw"];

    return json.dumps(settings_copy)

@web.route('/emailTest', method='POST')
def email_test():
    ''' Test the email settings, and return the result.'''
    email_from = request.forms.get('email_from')
    email_to = request.forms.get('email_to').split(',')
    passw = request.forms.get('email_pswd')
    smtp = request.forms.get('smtp')

    try:
        problems = sendemail(email_from, email_to, [], 'Test email from the thermostat',
            "This test was apparently successful", email_from, passw, smtp)
    
        if len(problems.items()) == 0:
            return "Test successful"

    except SMTPAuthenticationError as ae:
        return "SMTPAuthenticationError: username '%s' and password don't match" % email_from
    except SMTPResponseException as re:
        return "SMTP Exception (%d): %s" % (re.smtp_code, re.smtp_error)
    except SMTPRecipientsRefused as rr:
        return "Problem with recipient (%s):" % email_to
    except socket.error as err:
        return "Error connecting to '%s'" % smtp + " maybe you need the port (like smtp.gmail.com:587)"
    
    return str(problems)

def minutesToText(minutes):
    minutes = int(minutes)
    hours = int(minutes / 60) % 24
    time = '';
    if hours < 12:
        time = "A";
    else:
        time = "P";
    minutes = minutes % 60

    hours = hours % 12

    return '%d:%02d%s' % (hours, minutes, time)

@web.route('/')
def root():
    ''' Return the template, with the formatted data where the {{}} braces are.'''

    # store this information in key-value pairs so that the template engine can find them.
    indexInformation = {}

    indexInformation["ipaddress"] = os.uname()[1]
    
    indexInformation["days"] = days
    
    # replace parts of views/index.tpl with the information in the indexInformation dictionary.
    with settingsLock:
        times = {}
        for day in days:
            times[day + 'Morn'] = minutesToText(settings[day + 'Morn'])
            times[day + 'Night'] = minutesToText(settings[day + 'Night'])
        indexInformation["times"] = times

        indexInformation["settings"] = copy.copy(settings)

    log.info("Web page request for '/' from %s", request.remote_addr)
    
    return template('index', **indexInformation)

@web.route('/action', method='POST')
def action():
    ''' This method gets called from the ajax calls in javascript to do things from the forms. '''
    id = request.forms.get('id')
    print id
    
    if 'Enable' in id:
        print request.forms.get('value')
    
@web.route('/settings', method='POST')
def settings_post():
    ''' When the user "saves" their settings on the ConfigurePage. '''
    with settingsLock:
        settings["doHeat"] = bool(request.forms.get('doHeat', False))
        settings["doCool"] = bool(request.forms.get('doCool', False))

        settings["heatTempComfortable"] = float(request.forms.get('heatTempComfortable'))
        settings["heatTempSleeping"] = float(request.forms.get('heatTempSleeping'))
        settings["heatTempAway"] = float(request.forms.get('heatTempAway'))

        settings["coolTempComfortable"] = float(request.forms.get('coolTempComfortable'))
        settings["coolTempSleeping"] = float(request.forms.get('coolTempSleeping'))
        settings["coolTempAway"] = float(request.forms.get('coolTempAway'))

        settings["doEmail"] = bool(request.forms.get('doEmail', False))
        settings["smtp"] = request.forms.get('smtp')
        settings["email_from"] = request.forms.get('email_from')
        settings["email_to"] = request.forms.get('email_to')
        if len(request.forms.get('email_passw')) > 0:
            # only reset the password if one was entered. Sorry, there's no way to clear it... yet.
            settings["email_passw"] = request.forms.get('email_passw')
        settings["email_restart"] = bool(request.forms.get('email_restart', False))
        settings["email_oor"] = bool(request.forms.get('email_oor', False))

        for day in days:
            settings[day + "Morn"] = int(request.forms.get(day + "Morn"))
            settings[day + "Night"] = int(request.forms.get(day + "Night"))
            
        settings["apiKey"] = request.forms.get('apiKey')
        settings["weather_state"] = request.forms.get('weather_state')
        settings["weather_city"] = request.forms.get('weather_city')
        
        with open('settings.json', 'w') as fp:
            json.dump(settings, fp, sort_keys=True, indent=4)

def getUpdaterInfo():
    ''' returns a dictionary with variables defined for the updater template.'''
    # store this information in key-value pairs so that the template engine can find them.
    updaterInfo = \
    {
        "temperatureHistory" : '',
        "humidityHistory" : '',
        "heatHistory" : '',
        "updateTimeHistory" : '',
        "arduinoUptimeHistory" : '',
        "linuxUptimeHistory" : '',
        "flappyPingHistory" : '',
        "phonePingHistory" : '',
        "outsideTempHistory" : '',
    }
    
    with plotDataLock:
        for data in plotData:
            updaterInfo['temperatureHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["temperature"])
            updaterInfo['humidityHistory']      += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["humidity"])
            updaterInfo['heatHistory']          += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["heat"])
            updaterInfo['updateTimeHistory']    += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["lastUpdateTime"])
            updaterInfo['arduinoUptimeHistory'] += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["uptime_ms"])
            updaterInfo['linuxUptimeHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["py_uptime_ms"])
            updaterInfo['flappyPingHistory']    += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["flappy_ping"])
            updaterInfo['phonePingHistory']     += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["phone_ping"])
            if data["outside_temp_updated"]:
                updaterInfo['outsideTempHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["outside_temp"])

    # Add the outside brackets to each plot data.
    for key, value in updaterInfo.items():
        updaterInfo[key] = '[' + value + ']'

    updaterInfo["timezone"] = time.timezone * 1000.0

    return updaterInfo

# router for the jquery scripts
@web.route('/javascript/<path:path>')
def JavascriptCallback(path):
    
    if path == "updater.js":
        return template('updater', **getUpdaterInfo())
    
    if path == "forms.js":
        return template('forms', **getUpdaterInfo())
    
    ''' Just return any files in the javascript folder. '''
    return static_file('javascript/'+path, root='.')

# router for local static pages
@web.route('/static/<path:path>')
def staticPage(path):
    
    ''' Just return any files in the static folder. '''
    return static_file(path, root='static')

if __name__ == '__main__':
    
    log.info('Started at %s', str(datetime.datetime.now()))

    # create an instance of the query.
    query = QueryThread()
    
    # start the thread.
    query.start()
    
    # start the web server
    web.run(host='0.0.0.0', debug=True, server=PasteServer)
    
    # when the server stops, call quit on the thread.
    query.stop()
