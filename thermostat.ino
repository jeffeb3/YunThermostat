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

void setup() 
{
    // set the initial message to use during setup.
    display.OnetimeDisplay("Waiting for the ",
                           "Bridge          ");

    // Set up to toggle the builtin LED.
    pinMode(HEAT_PIN, OUTPUT);
    pinMode(COOL_PIN, OUTPUT);
  
    // Bridge startup, make the L13 LED go on, then initialize, then off.
    Bridge.begin();

    Bridge.put("heatSetPoint", String(HEAT_TEMP_DETACHED));
    Bridge.put("coolSetPoint", String(COOL_TEMP_DETACHED));

    web.Setup();
    
    // Clear the initial message now that we are set up.    
    display.OnetimeDisplay("                ",
                           "                ");
}

void loop() 
{
    // Update readings from the temperature sensor.
    sensor.Update();
    
    display.StatusDisplay();

    int button = display.GetButton();
    switch (button)
    {
        case LCD_BUTTON_NO_BUTTON:
            break;
        case LCD_BUTTON_UP       :
            Bridge.put("heatSetPoint", String(BridgeGetFloat("heatSetPoint") + 1.0));
            Bridge.put("lcdOverride", "true");
            break;
        case LCD_BUTTON_DOWN     :
            Bridge.put("heatSetPoint", String(BridgeGetFloat("heatSetPoint") - 1.0));
            Bridge.put("lcdOverride", "true");
            break;
        case LCD_BUTTON_LEFT     :
            break;
        case LCD_BUTTON_RIGHT    :
            break;
        case LCD_BUTTON_SELECT   :
            Bridge.put("heatSetPoint", String(web.GetPrevHeatSetPoint()));
            Bridge.put("coolSetPoint", String(web.GetPrevCoolSetPoint()));
            Bridge.put("lcdOverride", "false");
            break;
        default:
            break;
    }

    web.Update();
    
    // if the temperature is more than the hysteresis above the set point.
    if (sensor.GetTemperature() - BridgeGetFloat("heatSetPoint") > HEAT_SHUTOFF_HYSTERESIS)
    {
        // turn it off
        digitalWrite(HEAT_PIN, LOW);
        Bridge.put("heat", "0");
    }
    // else if the temperature is less than the hysteresis below the set point,
    else if (BridgeGetFloat("heatSetPoint") - sensor.GetTemperature() > HEAT_TURNON_HYSTERESIS)
    {
        // turn it on
        digitalWrite(HEAT_PIN, HIGH);
        Bridge.put("heat", "1");
    }
    
    // if the temperature is more than the hysteresis above the set point.
    if (sensor.GetTemperature() - BridgeGetFloat("coolSetPoint") > COOL_TURNON_HYSTERESIS)
    {
        // turn it on
        digitalWrite(COOL_PIN, HIGH);
        Bridge.put("cool", "1");
    }
    // else if the temperature is less than the hysteresis below the set point,
    else if (BridgeGetFloat("coolSetPoint") - sensor.GetTemperature() > COOL_SHUTOFF_HYSTERESIS)
    {
        // turn it off
        digitalWrite(COOL_PIN, HIGH);
        Bridge.put("cool", "0");
    }
    
    UpdateBridge();
    
    delay(50);
}

void UpdateBridge()
{
    Bridge.put("uptime_ms",String(millis()));
}

