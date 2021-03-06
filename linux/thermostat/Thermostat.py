
# The place where the thermostat runs.

# system imports
import commands
import copy
import datetime
import json
import logging
import threading
import time
import urllib
import urllib2
import mosquitto
import socket
from collections import deque

# local imports
import settings

def uptime():
    ''' get this system's seconds since starting '''
    with open('/proc/uptime', 'r') as f:
        uptime_seconds = float(f.readline().split()[0])
        return uptime_seconds

def freeMem():
    ''' get this system's free memory (unix only, sorry).'''
    text = commands.getoutput('free -m').split('\n')
    for line in text:
        if '-/+ buffers' in line:
            values = line.split()
            used = float(values[2])
            free = float(values[3])
            return used / (used + free)

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
        self.temperatureRange = (0.0, 0.0)
        self.overrideTemperatureRange = None
        self.overrideTemperatureType = None
        self.startTime = time.time()

        # cache
        self.outsideTemp = 0

        # state data history
        self.plotData = deque([], 60/5*24)
        self.recentHistory = deque([], 10) # deque will only keep maxlen items. I'm shooting for five minutes
        self.plotDataLock = threading.RLock()

        # log
        self.log = logging.getLogger('thermostat.Thermostat')

        # connect to mqtt
        self.mqtt_client = mosquitto.Mosquitto("Thermostat")
        self.mqtt_client.will_set("home/front_room/status", "Error", 0, True)
        # self.mqtt_client.username_pw_set(settings.Get("mqtt_user"), settings.Get("mqtt_pass"))
        self.mqtt_connected = False
        self.mqtt_client.on_connect = self.mqtt_on_connect
        self.mqtt_client.on_message = self.mqtt_on_message

        # Put the mwtt running stuff in it's own thread.
        self.mqtt_thread = threading.Thread(target=self.mqtt_run)
        self.mqtt_thread.daemon = True
        self.mqtt_thread.start()

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
                        self.log.debug('Retrieved outside temp:' + str(self.outsideTemp))
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
                data["linux_uptime_ms"] = uptime() * 1000.0
                data["linux_free_mem_perc"] = freeMem() * 100.0
                data["py_uptime_ms"] = (time.time() - self.startTime) * 1000.0
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

                self.log.debug('Arduino (%.1fs) -- T: %.1f H: %.1f', data["lastUpdateTime"] / 1000.0, data["temperature"], data["humidity"])

                with self.plotDataLock:
                    self.recentHistory.append(data)

                self.updatePlotData()

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

    def updatePlotData(self):
        ''' Add data to the plotData based on the recent history '''

        with self.plotDataLock:
            if len(self.plotData) == 0 or self.recentHistory[0]['time'] > self.plotData[-1]['time']:
                self.log.debug('updating plot data, len %d', len(self.plotData))
                data = copy.deepcopy(self.recentHistory[-1])

                # average some of the data
                sumOutsideTemp = 0.0
                countOutsideTemp = 0
                sumTemperature = 0.0
                sumHumidity = 0.0
                for pt in self.recentHistory:
                    sumTemperature += pt['temperature']
                    sumHumidity += pt['humidity']

                    if pt['outside_temp_updated']:
                        sumOutsideTemp += pt['outside_temp']
                        countOutsideTemp += 1

                    if pt['heat']:
                        data['heat'] = True

                    if pt['cool']:
                        data['cool'] = True

                if countOutsideTemp > 0:
                    data['outside_temp'] = sumOutsideTemp / countOutsideTemp
                    data['outside_temp_updated'] = True

                data['temperature'] = sumTemperature / len(self.recentHistory)
                data['humidity'] = sumHumidity / len(self.recentHistory)

                self.plotData.append(data)

    def getSetTemperatureRange(self):
        now = datetime.datetime.now()
        day = settings.DAYS[(now.weekday() + 1) % 7] # python says 0 is Monday.

        wakeUp = settings.Get(day + 'Morn')
        sleep = settings.Get(day + 'Night')

        minutes = now.minute + 60*now.hour
        if minutes < wakeUp:
            # we are still asleep
            if not self.sleeping:
                self.log.info('Started Sleeping')
                self.clearOverride()
            self.sleeping = True
        elif minutes < sleep:
            # we are just waking up
            if self.sleeping:
                self.log.info('Stopped Sleeping')
                self.clearOverride()
            self.sleeping = False
        else:
            # we went back to sleep
            if not self.sleeping:
                self.log.info('Started Sleeping')
                self.clearOverride()
            self.sleeping = True

        try:
            url = 'http://api.thingspeak.com/channels/' + settings.Get('thingspeak_location_channel') + '/feeds/last.json'
            url += '?key=' + settings.Get('thingspeak_location_api_key')
            new_away = ("0" == json.load(urllib2.urlopen(url))['field1'])
            if new_away != self.away:
                if new_away:
                    self.log.info('Setting to away')
                else:
                    self.log.info('Setting to home')
                self.clearOverride()
            self.away = new_away
        except Exception as e:
            # swallow any exceptions, we don't want the thermostat to break if there is no Internet
            self.log.exception(e)
            pass

        new_temp_range = self.temperatureRange
        if self.sleeping:
            new_temp_range = (settings.Get("heatTempSleeping"), settings.Get("coolTempSleeping"))
        else:
            if self.away:
                new_temp_range = (settings.Get("heatTempAway"), settings.Get("coolTempAway"))
            else:
                new_temp_range = (settings.Get("heatTempComfortable"), settings.Get("coolTempComfortable"))

        if new_temp_range != self.temperatureRange:
            if settings.Get('doCool'):
                self.log.info('Changed temperature range to %0.1f...%0.1f' % new_temp_range)
            else:
                self.log.info('Changed temperature to %0.1f' % new_temp_range[0])
            self.temperatureRange = new_temp_range

        if self.overrideTemperatureType is not None:
            return self.overrideTemperatureRange
        else:
            return self.temperatureRange

    def clearOverride(self):
        if self.overrideTemperatureType == 'temporary':
            self.log.info('removing temperature override.')
            self.overrideTemperatureRange = None
            self.overrideTemperatureType = None

    def setOverride(self, temperatureRangeTuple, temporary, permanent):
        """ Set an override. Either temporary, or permanent. """
        if not temporary and not permanent:
            self.overrideTemperatureRange = None
            self.overrideTemperatureType = None
            self.log.info("Clearing temperature override")

        if temporary:
            self.overrideTemperatureType = 'temporary'
            self.overrideTemperatureRange = temperatureRangeTuple
            if settings.Get('doCool'):
                self.log.info('Setting temporary override to %0.1f..%0.1f' % temperatureRangeTuple)
            else:
                self.log.info('Setting temporary override to %0.1f' % temperatureRangeTuple[0])

        if permanent:
            self.overrideTemperatureType = 'permanent'
            self.overrideTemperatureRange = temperatureRangeTuple
            if settings.Get('doCool'):
                self.log.info('Setting permanent override to %0.1f..%0.1f' % temperatureRangeTuple)
            else:
                self.log.info('Setting permanent override to %0.1f' % temperatureRangeTuple[0])

    def speak(self):
        """ Record last data to thingspeak. """
        if not settings.Get('doThingspeak'):
            # don't log to thing speak.
            return

        channelData = {}
        channelData['key'] = settings.Get("thingspeak_api_key")

        with self.plotDataLock:
            data = self.recentHistory[-1]

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
            if len(self.recentHistory) > 0:
	        return copy.deepcopy(self.recentHistory[-1])
	    else:
	        return None


    def getPlotHistory(self):
        ''' returns a dictionary with variables defined for the updater template.'''
        # store this information in key-value pairs so that the template engine can find them.
        updaterInfo = \
        {
            "temperatureHistory" : '',
            "outsideTempHistory" : '',
            "heatHistory" : '',
            "coolHistory" : '',

            "setHeatHistory" : '',
            "setCoolHistory" : '',
            "homeHistory" : '',
            "sleepHistory" : '',

            "updateTimeHistory" : '',
            "memHistory" : '',
        }

        with self.plotDataLock:
            for data in self.plotData:
                updaterInfo['temperatureHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["temperature"])
                if data["outside_temp_updated"]:
                    updaterInfo['outsideTempHistory']   += '[ %f, %f],' % (data["time"] - (time.timezone * 1000.0), data["outside_temp"])
                updaterInfo['heatHistory']          += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["heat"])
                updaterInfo['coolHistory']          += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["cool"])
                updaterInfo['setHeatHistory']       += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["heatSetPoint"])
                updaterInfo['setCoolHistory']       += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["coolSetPoint"])
                updaterInfo['homeHistory']          += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), 1 - data["away"])
                updaterInfo['sleepHistory']         += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["sleeping"])
                updaterInfo['updateTimeHistory']    += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["lastUpdateTime"])
                updaterInfo['memHistory']           += '[ %f, %d],' % (data["time"] - (time.timezone * 1000.0), data["linux_free_mem_perc"])

        # Add the outside brackets to each plot data.
        for key, value in updaterInfo.items():
            updaterInfo[key] = '[' + value + ']'

        return updaterInfo

    def mqtt_run(self):
        '''
        Do the mqtt stuff. Keeping it alive. Logging to it. taking commands from it, etc.
        '''
        while True:
            starttime = time.time()
            while (time.time() - starttime) < 30.0:
                time.sleep(0.5)

                # keep the mqtt alive.
                if 0 != self.mqtt_client.loop():
                    if self.mqtt_connected:
                        self.log.warning("MQTT Client Disconnected")
                    self.mqtt_connected = False

            data = self.copyData()
            if not data:
                continue

            # send the data to mqtt
            if not self.mqtt_connected:
                self.log.debug("Mqtt Connecting")
                try:
                    self.mqtt_client.connect(settings.Get("mqtt_addr"), settings.Get("mqtt_port"))
                except socket.error as e:
                    continue
                time.sleep(0.5)

            if self.mqtt_connected:
                self.mqtt_client.publish("home/front_room/temp", str(data["temperature"]), 0, True)
                self.mqtt_client.publish("home/front_room/humidity", str(data["humidity"]), 0, True)
                self.mqtt_client.publish("home/front_room/heat/desired_temp", str(data["heatSetPoint"]), 0, True)
                self.mqtt_client.publish("home/front_room/heat/active", "ON" if data["heat"] == 1 else "OFF", 0, True)
                self.mqtt_client.publish("home/front_room/cool/desired_temp", str(data["coolSetPoint"]), 0, True)
                self.mqtt_client.publish("home/front_room/cool/active", "ON" if data["cool"] == 1 else "OFF", 0, True)

    def mqtt_on_connect(self, mosq, obj, rc):
        self.log.debug("Received connection info: " + str(rc))
        if rc == 0:
            self.mqtt_connected = True
            self.mqtt_client.publish("home/front_room/status", "OK", 1, retain=True)
            self.mqtt_client.subscribe("home/front_room/heat/override_temp")
            self.log.info("MQTT Client Connected")

    def mqtt_on_message(self, mosq, obj, msg):
        if msg.topic == "home/front_room/heat/override_temp":
            self.log.info("received command from mqtt '" + str(msg.payload) + "'")
            try:
                heat_temp = int(msg.payload)
                self.setOverride((heat_temp, 80), True, False)
            except TypeError as e:
                self.log.exception(e)
                pass
        else:
            self.log.info("received unknown topic: %s", msg.topic)
