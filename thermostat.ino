// This sketch is the physical connection to the DHT22 temperature/humidity sensor and some output relays via the REST API

//-----------------------------------------------------------
// Local file includes
//-----------------------------------------------------------
#include "Config.h"
#include "Util.h"
#include "Sensor.h"
#include "Display.h"
#include "Web.h"

//-----------------------------------------------------------
// Arduino/System includes
//-----------------------------------------------------------
#include <Bridge.h>
#include <YunServer.h>
#include <YunClient.h>

//-----------------------------------------------------------
// Arduino helpers.
//  - Even though these aren't needed here, you have to add
// them to get the arduino toolchain to add them to the build
// command.
//-----------------------------------------------------------
#include <DHT.h>
#include <LiquidCrystal.h>

//-----------------------------------------------------------
// Global memory
//-----------------------------------------------------------
Sensor sensor;
Display display;
Web web;

// Thermostat variables, with defaults set.
float setPoint = HEAT_TEMP_DETACHED;
int setOverride = 0;

// The amount of time since the last temperature update.
unsigned long lastUpdateTime = 0;

void setup() 
{
    // set the initial message to use during setup.
    display.OnetimeDisplay("Waiting for the ",
                           "Bridge          ");

    // Set up to toggle the builtin LED.
    pinMode(13, OUTPUT);
  
    // Bridge startup, make the L13 LED go on, then initialize, then off.
    Bridge.begin();

    web.Setup();
    
    // Clear the initial message now that we are set up.    
    display.OnetimeDisplay("                ",
                           "                ");
  
    // restart this timer, now that the arduino is up.
    lastUpdateTime = millis();
}

void loop() 
{
    // Update readings from the temperature sensor.
    sensor.Update();
    
    display.StatusDisplay(sensor.GetTemperature(),
                          sensor.GetHumidity(),
                          setPoint,
                          80.0,
                          setOverride);

    int button = display.GetButton();
    switch (button)
    {
        case LCD_BUTTON_NO_BUTTON:
            break;
        case LCD_BUTTON_UP       :
            setPoint = setPoint + 1;
            setOverride = 1;
            break;
        case LCD_BUTTON_DOWN     :
            setPoint = setPoint - 1;
            setOverride = 1;      
            break;
        case LCD_BUTTON_LEFT     :
            break;
        case LCD_BUTTON_RIGHT    :
            break;
        case LCD_BUTTON_SELECT   :
            // need to get setPoint from Linux here
            setOverride = 0;        
            break;
        default:
            break;
    }

    web.Update();
    
    // if the temperature is more than the hysteresis above the set point.
    if (sensor.GetTemperature() - setPoint > HEAT_SHUTOFF_HYSTERESIS)
    {
        // turn it off
        digitalWrite(13, LOW);
    }
    // else if the temperature is less than the hysteresis below the set point,
    else if (setPoint - sensor.GetTemperature() > HEAT_TURNON_HYSTERESIS)
    {
        // turn it on
        digitalWrite(13, HIGH);
    }
    
    delay(50);
}

