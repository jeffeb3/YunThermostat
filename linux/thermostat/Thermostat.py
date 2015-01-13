
# The place where the thermostat runs.

# system imports
import copy
import datetime
import json
import logging
import threading
import time
import urllib
import urllib2

# local imports
import settings

def uptime():
    ''' get this system's seconds since starting '''    
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

class Thermostat(threading.Thread):
    """
    Thermostat contains the main loop, and anything that aren't big
    enough for their own module/file. There should be no web here.
    """

    def __init__(self):
        """
        Creates a thread (but doesn't start it).
        :logHandlers: A list of logging.handlers to append to my log.
        """
        threading.Thread.__init__(self)
        # Set to daemon so the main thread will exit even if this is still going.
        self.daemon = True 

        # run these events right away.
        self.lastLoopTime = 0
        self.lastOutsideMeasurementTime = 0

        # state
        self.sleeping = False
        self.away = False
        
        # cache
        self.outsideTemp = 0

        # state data history
        self.plotData = []
        self.plotDataLock = threading.RLock()

        # log
        self.log = logging.getLogger('thermostat.Thermostat')
    
    def run(self):
        """
        Main loop for the thermostat project. Reads data from external sources,
        updates internal data, and sends data out to data recorders.
        """
        self.log.info('Starting the Thermostat Thread');
        while True:     # Forever
            # this try...except block is to log all exceptions. It's in this
            # while loop because the while loop should recover.
            try:
                # sleep a moment at a time, so that we can catch the quit signal
                while (time.time() - self.lastLoopTime) < 30.0:
                    time.sleep(0.5)

                self.lastLoopTime = time.time()
    
                # Gather data from Wunderground, but only every 10 minutes (limited for free api account)
                outsideTempUpdated = False
                if ((time.time() - self.lastOutsideMeasurementTime) > 360):
                    try:
                        outsideData = json.load(urllib2.urlopen("http://api.wunderground.com/api/" +
                                                                settings.Get("weather_api_key") + "/conditions/q/" +
                                                                settings.Get("weather_state") + '/' + settings.Get("weather_city") + ".json"))
                        self.outsideTemp = outsideData['current_observation']['temp_f']
                        self.log.info('Retrieved outside temp:' + str(self.outsideTemp))
                        outsideTempUpdated = True
                        self.lastOutsideMeasurementTime = time.time()
                    except Exception as e:
                        # swallow any exceptions, we don't want the thermostat to break if there is no Internet
                        self.log.exception(e)
                        pass
    
                # ping the server
                heartbeat = json.load(urllib2.urlopen("http://" + settings.Get("arduino_addr") + "/arduino/heartbeat"));
    
                # Get data from server.
                data = json.load(urllib2.urlopen("http://" + settings.Get("arduino_addr") + "/data/get/"));
                data = data["value"]
                data["time"] = time.time() * 1000.0
                data["py_uptime_ms"] = uptime() * 1000.0
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
                
                self.log.info('Arduino (%.1fs) -- T: %.1f H: %.1f', data["lastUpdateTime"] / 1000.0, data["temperature"], data["humidity"])
                
                with self.plotDataLock:
                    self.plotData.append(data)
                    self.plotData = self.plotData[-2880:] # clip to 24 hours
    
                try:
                    self.speak()
                except Exception as e:
                    self.log.exception(e)
    
                # Calculate what the set point should be
                setRange = self.getSetTemperatureRange()
                
                # send the set point to the arduino
                urllib2.urlopen("http://" + settings.Get("arduino_addr") + "/arduino/command/" + str(setRange[0]) + "/" + str(setRange[1]))
    
            except Exception as e:
                self.log.exception(e)
                time.sleep(60.0) # sleep for extra long.
                continue
    
    def getSetTemperatureRange(self):
        now = datetime.datetime.now()
        day = settings.DAYS[(now.weekday() + 1) % 7] # python says 0 is Monday.

        wakeUp = settings.Get(day + 'Morn')
        sleep = settings.Get(day + 'Night')
        
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
        
        if self.sleeping:
            return (settings.Get("heatTempSleeping"), settings.Get("coolTempSleeping"))
        else:
            return (settings.Get("heatTempComfortable"), settings.Get("coolTempComfortable"))

    def speak(self):
        """ Record last data to thingspeak. """
        if not settings.Get('doThingspeak'):
            # don't log to thing speak.
            return

        channelData = {}
        channelData['key'] = settings.Get("thingspeak_api_key")

        with self.plotDataLock:
            data = self.plotData[-1]
        
            channelData['field1'] = data['temperature']
            if data["outside_temp_updated"]:
                channelData['field2'] = data['outside_temp']
            channelData['field3'] = data['heat']
            channelData['field4'] = data['heatSetPoint']
            channelData['field5'] = data['cool']
            channelData['field6'] = data['coolSetPoint']
            channelData['field7'] = data['uptime_ms'] / 1000.0
            channelData['field8'] = data['py_uptime_ms'] / 1000.0

        headers = \
        {
            'Content-type': 'application/x-www-form-urlencoded',
            'Accept': 'text/plain'
        }
        enc = urllib.urlencode(channelData)
        req = urllib2.Request('https://api.thingspeak.com/update', enc, headers)
        response = urllib2.urlopen(req)

    def copyData(self):
        """ Retrieve the latest data. """
        with self.plotDataLock:
            return copy.copy(self.plotData[-1])

    
    def getPlotHistory(self):
        ''' returns a dictionary with variables defined for the updater template.'''
        # store this information in key-value pairs so that the template engine can find them.
        updaterInfo = \
        {
            "temperatureHistory" : '',
            "outsideTempHistory" : '',
            "heatHistory" : '',
            "updateTimeHistory" : '',
        }
        
        with self.plotDataLock:
            for data in self.plotData:
                updaterInfo['temperatureHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["temperature"])
                if data["outside_temp_updated"]:
                    updaterInfo['outsideTempHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["outside_temp"])
                updaterInfo['heatHistory']          += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["heat"])
                updaterInfo['updateTimeHistory']    += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["lastUpdateTime"])
    
        # Add the outside brackets to each plot data.
        for key, value in updaterInfo.items():
            updaterInfo[key] = '[' + value + ']'
    
        return updaterInfo
