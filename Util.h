
#ifndef THERMOSTAT_UTIL_H_
#define THERMOSTAT_UTIL_H_

#include <Bridge.h>

// Gamma LED correction. Taken from:
// https://learn.adafruit.com/led-tricks-gamma-correction?view=all
// 
const uint8_t PROGMEM gammaArray[] = {
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1,
    1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2,
    2, 3, 3, 3, 3, 3, 3, 3, 4, 4, 4, 4, 4, 5, 5, 5,
    5, 6, 6, 6, 6, 7, 7, 7, 7, 8, 8, 8, 9, 9, 9, 10,
    10, 10, 11, 11, 11, 12, 12, 13, 13, 13, 14, 14, 15, 15, 16, 16,
    17, 17, 18, 18, 19, 19, 20, 20, 21, 21, 22, 22, 23, 24, 24, 25,
    25, 26, 27, 27, 28, 29, 29, 30, 31, 32, 32, 33, 34, 35, 35, 36,
    37, 38, 39, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 50,
    51, 52, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 66, 67, 68,
    69, 70, 72, 73, 74, 75, 77, 78, 79, 81, 82, 83, 85, 86, 87, 89,
    90, 92, 93, 95, 96, 98, 99,101,102,104,105,107,109,110,112,114,
    115,117,119,120,122,124,126,127,129,131,133,135,137,138,140,142,
    144,146,148,150,152,154,156,158,160,162,164,167,169,171,173,175,
    177,180,182,184,186,189,191,193,196,198,200,203,205,208,210,213,
    215,218,220,223,225,228,231,233,236,239,241,244,247,249,252,255 };

// write to the pwm pin by using the value from the gamma table
void gammaWrite(int pin, uint8_t intensity)
{
    analogWrite(pin, pgm_read_byte(&gammaArray[intensity]));
}

// Smooth out a noisy signal.
// @param data The instantaneous data from a noise source.
// @param filterVal [0,1]] The higher, the more the instantaneous measurement is used.
// @param smoothedVal The previous smooth value.
// @return the smoothedVal, use this next time there is another measurement.
float smooth(float data, float filterVal, float smoothedVal)
{
    if (filterVal > 0.99)
    {      // check to make sure param's are within range
        filterVal = .99;
    }
    else if (filterVal <= 0)
    {
        filterVal = 0;
    }
    
    smoothedVal = (data * (1 - filterVal)) + (smoothedVal  *  filterVal);
  
    return smoothedVal;
}

// call Bridge.Get(pName,...) and convert the response to a float
float BridgeGetFloat(const char* pName)
{
    // not re-entrant...
    static char buffer[20];
    
    Bridge.get(pName, buffer, 20);
    
    return atof(buffer);
}

// call Bridge.Get(pName,...) and convert the response to an unsigned long
unsigned long BridgeGetULong(const char* pName)
{
    // not re-entrant...
    static char buffer[20];
    
    Bridge.get(pName, buffer, 20);
    
    return atol(buffer);
}

// call Bridge.Get(pName,...) and convert the response to a bool
bool BridgeGetBool(const char* pName)
{
    // not re-entrant...
    static char buffer[20];
    
    Bridge.get(pName, buffer, 20);

    if (buffer[0] == 0)
    {
        return false;
    }
    
    if (buffer[0] == 'T' or
        buffer[0] == 't')
    {
        return true;
    }
    
    if (atoi(buffer) > 0)
    {
        return true;
    }
    
    return false;
}

// call Bridge.Put(pName,...) and convert the value to a string
void BridgePutFloat(const char* pName, float value)
{
    Bridge.put(pName, String(value));
}


#endif // INCLUDE GUARD

