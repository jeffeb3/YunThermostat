// This file contains the thermostat control law

#ifndef CONTROL_H_
#define CONTROL_H_

//-----------------------------------------------------------
// Local includes
//-----------------------------------------------------------
#include "Config.h"
#include "Util.h"

//-----------------------------------------------------------
// Arduino/System includes
//-----------------------------------------------------------
#include <Bridge.h>

//-----------------------------------------------------------
// Library includes
//-----------------------------------------------------------

//-----------------------------------------------------------
// Global memory
//-----------------------------------------------------------

class Control
{
public:
    Control();
    
    void Update();
    void FastUpdate();
    
private:
    unsigned long lastUpdateTime;
    volatile unsigned long heatOnTime;
};

Control::Control() :
    lastUpdateTime(0),
    heatOnTime(0)
{
    // Set up to toggle the builtin LED.
    pinMode(HEAT_PIN, OUTPUT);
    digitalWrite(HEAT_PIN, HIGH);
    pinMode(RED_LED_PIN, OUTPUT);
    digitalWrite(RED_LED_PIN, HIGH);
    pinMode(COOL_PIN, OUTPUT);
}

void Control::FastUpdate()
{
    if (heatOnTime > 0)
    {
        unsigned long delta = ((millis() - heatOnTime)/3) % 500;
        if (delta < 250)
        {
            // up
            gammaWrite(RED_LED_PIN, 255 - delta);
        }
        else
        {
            // down
            delta -= 250;
            gammaWrite(RED_LED_PIN, delta);
        }
    }
    else
    {
        digitalWrite(RED_LED_PIN, HIGH);
    }
}

void Control::Update()
{
    if ((millis() - lastUpdateTime) < 1000)
    {
        return;
    }
    
    // if the temperature is more than the hysteresis above the set point.
    if (BridgeGetFloat("temperature") - BridgeGetFloat("heatSetPoint") > HEAT_SHUTOFF_HYSTERESIS)
    {
        // turn it off
        digitalWrite(HEAT_PIN, HIGH);
        heatOnTime = 0;
        Bridge.put("heat", "0");
    }
    // else if the temperature is less than the hysteresis below the set point,
    else if (BridgeGetFloat("heatSetPoint") - BridgeGetFloat("temperature") > HEAT_TURNON_HYSTERESIS)
    {
        // turn it on
        digitalWrite(HEAT_PIN, LOW);
        if (heatOnTime == 0)
        {
            heatOnTime = millis();
        }
        Bridge.put("heat", "1");
    }
    
    // if the temperature is more than the hysteresis above the set point.
    if (BridgeGetFloat("temperature") - BridgeGetFloat("coolSetPoint") > COOL_TURNON_HYSTERESIS)
    {
        // turn it on
        digitalWrite(COOL_PIN, HIGH);
        Bridge.put("cool", "1");
    }
    // else if the temperature is less than the hysteresis below the set point,
    else if (BridgeGetFloat("coolSetPoint") - BridgeGetFloat("temperature") > COOL_SHUTOFF_HYSTERESIS)
    {
        // turn it off
        digitalWrite(COOL_PIN, HIGH);
        Bridge.put("cool", "0");
    }

    Bridge.put("uptime_ms",String(millis()));
}

#endif // INCLUDE_GUARD