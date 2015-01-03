// This is a configuration file for the thermostat project.

#ifndef THERMOSTAT_CONFIG_H_
#define THERMOSTAT_CONFIG_H_

//-----------------------------------------------------------
// DHT Pins
//-----------------------------------------------------------
#define DHT_VCC_PIN A1
#define DHT_DATA_PIN A2
#define DHT_GND_PIN A3

#define DHT_TYPE DHT22

//-----------------------------------------------------------
// LCD Pins
//-----------------------------------------------------------
// Pins used in LiquidCrystal()
#define LCD_PIN_0 8
#define LCD_PIN_1 9
#define LCD_PIN_2 4
#define LCD_PIN_3 5
#define LCD_PIN_4 6
#define LCD_PIN_5 7

// Pin where the LCD buttons are attached
#define LCD_BUTTONS_PIN 0

//-----------------------------------------------------------
// Thermostat Settings
//-----------------------------------------------------------

// This temperature will be the heater set point until a more clever application
// connects
#define HEAT_TEMP_DETACHED 68.0

// When the temperature is this amount more than the set point, the heat will
// turn off.
#define HEAT_SHUTOFF_HYSTERESIS 0.75

// When the temperature is this amount less than the set point, the heat will
// turn on.
#define HEAT_TURNON_HYSTERESIS 0.5



#endif // include guard
