
# A place to store all the settings in a thread-safe (blocking) way.
# 
# Settings just for the thermostat, of course.

import copy
import json
import threading

# ------- Module Data (Singletonish) -------

settingsLock = threading.RLock()
# Don't read this directly, use the methods below.
settings = {}

DAYS = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]

def Load(filename):
    """
    Loads the settings from a (JSON) file. Will succeed no matter what.
    """
    try:
        with open(filename, 'r') as fp:
            global settingsLock
            global settings
            with settingsLock:
                settings = json.load(fp)
                return True
    except Exception:
        return False
    
def FillEmptiesWithDefaults():
    """
    If the settings is missing items, or there just weren't any to
    begin with, this will make it a complete settings object.
    """
    default_settings = {}
    
    # These are the initial settings for the configuration page.
    default_settings["doHeat"] = True
    default_settings["doCool"] = True

    default_settings["heatTempComfortable"] = 68.0
    default_settings["heatTempSleeping"] = 62.0
    default_settings["heatTempAway"] = 62.0

    default_settings["coolTempComfortable"] = 76.0
    default_settings["coolTempSleeping"] = 72.0
    default_settings["coolTempAway"] = 78.0

    default_settings["doEmail"] = True
    default_settings["smtp"] = 'smtp.gmail.com:587'
    default_settings["email_from"] = ''
    default_settings["email_to"] = ''
    default_settings["email_passw"] = ''
    default_settings["email_restart"] = True
    default_settings["email_oor"] = True

    for day in DAYS:
        default_settings[day + "Night"] = 1320
        default_settings[day + "Morn"] = 360
    
    default_settings["weather_api_key"] = ''
    default_settings["weather_state"] = 'CO'
    default_settings["weather_city"] = 'Denver'

    default_settings["doThingspeak"] = False
    default_settings["thingspeak_api_key"] = ''
    default_settings["thingspeak_location_api_key"] = ''
    default_settings["thingspeak_location_channel"] = ''
    
    # secret settings (not on the web page).
    default_settings["arduino_addr"] = "localhost"
    
    global settingsLock
    global settings
    with settingsLock:
        settings = dict(default_settings.items() + settings.items())

def Save(filename):
    """
    Save the settings to a (JSON) file. It will raise exceptions if it can't be done.
    """
    with open(filename, 'w') as fp:
        with settingsLock:  
            json.dump(settings, fp, sort_keys=True, indent=4)

def Get(settingName):
    """
    Return the setting defined by settingName.
    
    :settingName: Key of the setting.
    raises KeyError when the name isn't present.
    """
    with settingsLock:
        return settings[settingName]

def Set(settingName, value):
    """
    Set the setting defined by settingName to value

    :settingName: Key of the setting.
    :value: Key of the setting.
    raises KeyError when the name isn't present.
    """
    with settingsLock:
        if settingName not in settings.keys():
            raise KeyError
        
        settings[settingName] = value

def Copy():
    """ return a new copy of the settings. """
    with settingsLock:
        return copy.copy(settings)
    
    