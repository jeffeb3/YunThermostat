
# system imports
import json
import logging
import os
import socket
from smtplib import SMTPAuthenticationError, SMTPResponseException, SMTPRecipientsRefused
import time

# Import bottle library.
from bottle import Bottle
from bottle import static_file, template, response, request

# local imports
import settings
from email_utils import sendemail

class Web(object):
    
    def __init__(self, thermostat):
        """
        Web interface for the thermostat.
        
        :thermostat: The Thermostat class.
        """

        self.log = logging.getLogger('thermostat.Web')
        
        self.web = Bottle()
        self.thermostat = thermostat
        
        # set up the routes. I'm not sure how to do this with decorators
        self.web.route('/', 'GET', self.root)
        self.web.route('/measurements', 'GET', self.measurementSse)
        self.web.route('/data.json', 'GET', self.daq)
        self.web.route('/settings', 'GET', self.settings_get)
        self.web.route('/emailTest', 'POST', self.email_test)
        self.web.route('/action', 'POST', self.action)
        self.web.route('/settings', 'POST', self.settings_post)
        self.web.route('/javascript/<path:path>', 'GET', self.javascriptCallback)
        self.web.route('/static/<path:path>', 'GET', self.staticPage)

    def measurementSse(self):
        '''  Generator function to connect to the YunServer instance and send
             all data received from it to the webpage as HTML5 server sent events. '''
    
        # Convert the response to an event stream.
        response.content_type = 'text/event-stream'
        
        previous_time = 0
    
        while True:
            # Send the data to the web page in the server sent event format.
            data = self.thermostat.copyData()
            if data["time"] == previous_time:
                time.sleep(0.5)
                continue

            previous_time = data["time"]            
            yield 'data: %s\n\n' % json.dumps(data)
    
    def daq(self):
        '''  Respond with a single json object, the most recent data. '''
        # Send the data to the web page in the server sent event format.
        return json.dumps(self.thermostat.copyData(), indent=4)
    
    def settings_get(self):
        '''  Generator function to send updates of the settings to the web page. '''
        settings_copy = settings.Copy()
        # Don't send the password out. We have enough security problems...
        del settings_copy["email_passw"];
        return json.dumps(settings_copy)
    
    def email_test(self):
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

    @staticmethod    
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
    
    def action(self):
        ''' This method gets called from the ajax calls in javascript to do things from the forms. '''
        id = request.forms.get('id')
        print id
        
        if 'Enable' in id:
            print request.forms.get('value')
        
    def settings_post(self):
        ''' When the user "saves" their settings on the ConfigurePage. '''
        settings.Set("doHeat",  bool(request.forms.get('doHeat', False)))
        settings.Set("doCool",  bool(request.forms.get('doCool', False)))
    
        settings.Set("heatTempComfortable",  float(request.forms.get('heatTempComfortable')))
        settings.Set("heatTempSleeping",  float(request.forms.get('heatTempSleeping')))
        settings.Set("heatTempAway",  float(request.forms.get('heatTempAway')))
    
        settings.Set("coolTempComfortable",  float(request.forms.get('coolTempComfortable')))
        settings.Set("coolTempSleeping",  float(request.forms.get('coolTempSleeping')))
        settings.Set("coolTempAway",  float(request.forms.get('coolTempAway')))
    
        settings.Set("doEmail",  bool(request.forms.get('doEmail', False)))
        settings.Set("smtp",  request.forms.get('smtp'))
        settings.Set("email_from",  request.forms.get('email_from'))
        if len(request.forms.get('email_passw')) > 0:
            # only reset the password if one was entered. Sorry, there's no way to clear it... yet.
            settings.Set("email_passw",  request.forms.get('email_passw'))
        settings.Set("email_to",  request.forms.get('email_to'))
        settings.Set("email_restart",  bool(request.forms.get('email_restart', False)))
        settings.Set("email_oor",  bool(request.forms.get('email_oor', False)))
    
        settings.Set("weather_api_key",  request.forms.get('weather_api_key'))
        settings.Set("weather_state",  request.forms.get('weather_state'))
        settings.Set("weather_city",  request.forms.get('weather_city'))
    
        settings.Set("doThingspeak",  bool(request.forms.get('doThingspeak', False)))
        settings.Set("thingspeak_api_key",  request.forms.get('thingspeak_api_key'))
    
        for day in settings.DAYS:
            settings.Set(day + "Morn",  int(request.forms.get(day + "Morn")))
            settings.Set(day + "Night",  int(request.forms.get(day + "Night")))
    
        settings.Save('settings.json')
    
    def javascriptCallback(self, path):
    
        if path == "updater.js":
            return template('updater', timezone = time.timezone * 1000.0, **self.thermostat.getPlotHistory())
        
        if path == "forms.js":
            return template('forms', timezone = time.timezone * 1000.0)
        
        ''' Just return any files in the javascript folder. '''
        return static_file('javascript/'+path, root='.')
    
    def staticPage(self, path):
        ''' Just return any files in the static folder. '''
        return static_file(path, root='static')
    
    def root(self):
        ''' Return the template, with the formatted data where the {{}} braces are.'''
    
        # store this information in key-value pairs so that the template engine can find them.
        indexInformation = {}
    
        indexInformation["ipaddress"] = os.uname()[1]
        
        indexInformation["days"] = settings.DAYS
        
        # replace parts of views/index.tpl with the information in the indexInformation dictionary.
        times = {}
        for day in settings.DAYS:
            times[day + 'Morn'] = Web.minutesToText(settings.Get(day + 'Morn'))
            times[day + 'Night'] = Web.minutesToText(settings.Get(day + 'Night'))
        indexInformation["times"] = times
    
        indexInformation["settings"] = settings.Copy()
    
        self.log.info("Web page request for '/' from %s", request.remote_addr)
        
        return template('index', **indexInformation)

    def run(self):
        """
        call the run method on the bottle server.
        """
        self.web.run(host='0.0.0.0', debug=True, server='paste')
