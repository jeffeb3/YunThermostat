// This sketch is the physical connection to the DHT22 temperature/humidity sensor and some output relays via the REST API

//-----------------------------------------------------------
// Local file includes
//-----------------------------------------------------------
#include "Config.h"
#include "Util.h"
#include "Control.h"
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
Control control;

SIGNAL(TIMER0_COMPA_vect)
{
    // This is the interrupt service routine for fast updates.
    //
    // This gets called once per millisecond.
    //
    // Don't put anything really long in here, such as external comms.
    //
    // Don't use delay.
    //
    control.FastUpdate();
    display.FastUpdate();
}

void setup() 
{
    delay(2500);
    // set the initial message to use during setup.
    display.OnetimeDisplay("Waiting for the ",
                           "Bridge          ");

    // Bridge startup, make the L13 LED go on, then initialize, then off.
    Bridge.begin();

    Bridge.put("heatSetPoint", String(HEAT_TEMP_DETACHED));
    Bridge.put("coolSetPoint", String(COOL_TEMP_DETACHED));
    Bridge.put("heat", "0");

    web.Setup();
    
    // Clear the initial message now that we are set up.    
    display.OnetimeDisplay("                ",
                           "                ");

    // When the counter passes this number, call the ISR
    OCR0A = 0xAF;
    // Interrupt Enable on timer 0, compare A. This always calls via TIMER0_COMPA_vect
    TIMSK0 |= _BV(OCIE0A);
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

    control.Update();    
}

