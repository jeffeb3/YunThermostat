
#ifndef THERMOSTAT_UTIL_H_
#define THERMOSTAT_UTIL_H_

#include <Bridge.h>

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
    
    return atoi(buffer);
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

