// All the code for reading the sensor is stored in this file

#ifndef THERMOSTAT_SENSOR_H_
#define THERMOSTAT_SENSOR_H_

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
#include <DHT.h>

//-----------------------------------------------------------
// Global memory
//-----------------------------------------------------------
DHT dht(DHT_DATA_PIN, DHT_TYPE);

class Sensor
{
public:
    inline Sensor() :
        dht(DHT_DATA_PIN, DHT_TYPE),
        temperatureLPF(0.5),
        humidityLPF(0.2),
        temperature(72.0),
        humidity(20.0),
        lastUpdateMillis(millis())
    {
        // Use the pins to power the DHT. It's easier than using jumpers
        pinMode(DHT_VCC_PIN,OUTPUT);
        pinMode(DHT_GND_PIN,OUTPUT);
        digitalWrite(DHT_VCC_PIN,HIGH);
        digitalWrite(DHT_GND_PIN,LOW);
    }
    
    // Call this function frequently, it will not hurt to call it too
    // frequently.
    inline void Update();

    // Returns the temperature in Farenheit.    
    inline float GetTemperature() const
    {
        return temperature;
    }
    
    // Returns the humidty in Percent.
    inline float GetHumidity() const
    {
        return humidity;
    }
    
private:
    DHT dht;
    
    float temperatureLPF = 0.5;
    float humidityLPF = 0.5;
    float temperature;
    float humidity;
    float lastUpdateMillis;
};

inline void Sensor::Update()
{
    if ((millis() - lastUpdateMillis) < 2000)
    {
        // The DHT library won't check more frequently than every two seconds,
        // so just don't update anything
        return;
    }
    
    float newTemp = dht.readTemperature(true);
    float newHumidity = dht.readHumidity();
    if (isnan(newTemp) or isnan(humidity))
    {
        // There was a problem with the sensor library, don't accept this measurement.
        return;
    }
    
    temperature = smooth(newTemp, temperatureLPF, temperature);
    humidity = smooth(newHumidity, humidityLPF, humidity);

    // Store the values in the Bridge.    
    BridgePutFloat("temperature", temperature);
    BridgePutFloat("humidity", humidity);

    lastUpdateMillis = millis();
}

#endif // INCLUDE GUARD

