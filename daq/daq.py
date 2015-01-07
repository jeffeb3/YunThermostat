#!/usr/bin/env python

# This is a utility to contain the interface to record data in the thermostat project.
#
# TODO:
# - Add the worksheet if it doesn't exist
# - Add the sheet if it doesn't exist
# - Handle the errors in http better (record them maybe)
# - Figure out a way that this program doesn't need to know what is inside data
# - Handle changed in data smoothly
# - Make it possible to copy a template spreadsheet from somewhere (possibly
#   checked into git) and insert data into it, with all the bells and whistles
# - Add a comment/status line that will show up as events in the graph.
#   - Add status for reboots.

# import python libraries
import datetime, time, json, urllib2, sys
from optparse import OptionParser

# The interface to the google account
import gspread

class daq(object):
    '''Utility class to record data to a google spreadsheet'''
    
    def __init__(self, username, passw):
        self.auth = (username, passw)
        self.problems = 0
        self.titles = ["time",
                       "temperature",
                       "outside_temp",
                       "humidity",
                       "heatSetPoint",
                       "coolSetPoint",
                       "sleeping",
                       "away",
                       "lcdOverride",
                       "heat",
                       "cool",
                       "lastUpdateTime",
                       "uptime_ms",
                       "py_uptime_ms",
                       "DAQ Problems"
                      ]
        
    def append(self, data):
        row = []

        data["DAQ Problems"] = self.problems
        for title in self.titles:
            # treat time in a special way.
            if title == 'time':
                row = [str(datetime.datetime.fromtimestamp(data["time"] / 1000.0))]
            else:
                row.append(data[title])

        try:
            worksheet = self.getWorksheet()
            worksheet.append_row(row)
        except KeyboardInterrupt as e:
            raise e
        except gspread.exceptions.SpreadsheetNotFound as e:
            print "The spreadsheet 'thermodaq' was not found. Please create it (I can't)."
            raise e
        except gspread.exceptions.AuthenticationError as e:
            print "Invalid Username and Password"
            raise e
        except:
            # I shouldn't swallow exceptions, but this thing is buggy...
            self.problems += 1
            print 'problem posting to gspread'
            pass
    
    def getClient(self):
        client = gspread.Client(auth=self.auth);
        client.login()
        return client
    
    def getWorksheet(self):
        client = self.getClient()
        ss = None
        ss = client.open('thermodaq')
        
        ws = None
        try:
            ws = ss.worksheet('daq')
        except gspread.exceptions.WorksheetNotFound as e:
            ws = ss.add_worksheet('daq', 1, len(self.titles))
            for index, title in enumerate(self.titles):
                ws.update_cell(1, 1+index, title)
        
        # check for new titles
        if ws.col_count < len(self.titles):
            for title in self.titles[ws.col_count:]:
                ws.add_cols(1)
                ws.update_cell(1,ws.col_count, title)

        return ws
    
if __name__ == '__main__':

    parser = OptionParser()
    parser.add_option('-u', "--username", dest="username", help="google username")
    parser.add_option('-p', "--password", dest="password", help="google password")
    parser.add_option('-i', "--ip", dest="ip", help="arduino url")
    (options, args) = parser.parse_args()
    
    if options.username == None or options.password == None or options.ip == None:
        print 'You have to supply a username, password, and an ip'
        parser.print_help()
        sys.exit(1)

    dataAcq = daq(options.username, options.password)
    addr = "http://" + options.ip + ":8080/data.json"
    print 'connecting to: ' + addr
    count = 0    
    while True:
        startTime = time.time()
        try:
            data = json.load(urllib2.urlopen(addr))
        except urllib2.URLError:
            print "The server (%s) isn't responding." % addr
            time.sleep(600)
            continue
        if data == None:
            time.sleep(1)
            continue
        
        dataAcq.append(data)
        count += 1
        if count % 100 == 0:
            print '%d sent' % count 
        seconds_left = 30.0 - (time.time() - startTime)
        if seconds_left > 0.0:
            time.sleep(30.0 - (time.time() - startTime))
