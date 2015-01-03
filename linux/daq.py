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

# import python libraries
import datetime

# The interface to the google account
import gspread

class daq(object):
    '''Utility class to record data to a google spreadsheet'''
    
    def __init__(self, username, passw):
        self.auth = (username, passw)
        self.problems = 0
    
    def append(self, data):
        row = [str(datetime.datetime.fromtimestamp(data["time"] / 1000.0))]
        row.append(data["temperature"])
        row.append(data["humidity"])
        row.append(data["heat"])
        row.append(data["cool"])
        row.append(data["setPoint"])
        row.append(data["setOverride"])
        row.append(data["lastUpdateTime"])
        row.append(data["uptime_ms"])
        row.append(data["py_uptime_ms"])
        row.append(self.problems)

        try:
            client = gspread.Client(auth=self.auth);
            client.login()
            spreadsheet = client.open('thermodaq')
            worksheet = spreadsheet.worksheet('daq')
            worksheet.append_row(row)
        except:
            # I shouldn't swallow exceptions, but this thing is buggy...
            self.problems += 1
            print 'problem posting to gspread'
            pass