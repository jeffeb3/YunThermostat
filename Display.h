// This file contains interface information for the display

#ifndef THERMOSTAT_DISPLAY_H_
#define THERMOSTAT_DISPLAY_H_

#include "Config.h"
#include <LiquidCrystal.h>

#define LCD_BUTTON_NO_BUTTON 0
#define LCD_BUTTON_UP        1
#define LCD_BUTTON_DOWN      2
#define LCD_BUTTON_LEFT      3
#define LCD_BUTTON_RIGHT     4
#define LCD_BUTTON_SELECT    5

class Display
{
public:
    Display();
    
    // Call this function to send a one time message. It will be displayed until
    // another display function is called.
    inline void OnetimeDisplay(char* pFirstLine, char* pSecondLine);
    
    // This displays the current operating status of the Thermostat.
    inline void StatusDisplay();
    
    inline int GetButton();
    
    // Quickly update the backlight.
    inline void FastUpdate();

private:
    LiquidCrystal lcd;
    unsigned long lastPythonUpdateMillis;
    char twiddle;
    int lastButton;
    unsigned long lastDrawTime;
    volatile unsigned long lastButtonPressTime;
};

Display::Display() :
    lcd(LCD_PIN_0,
        LCD_PIN_1,
        LCD_PIN_2,
        LCD_PIN_3,
        LCD_PIN_4,
        LCD_PIN_5),
    lastPythonUpdateMillis(millis()),
    twiddle(' '),
    lastButton(255),
    lastDrawTime(0),
    lastButtonPressTime(0)
{
    // set up the LCD's number of columns and rows:
    lcd.begin(16, 2);
    pinMode(LCD_BACKLIGHT_PIN, OUTPUT);
    digitalWrite(LCD_BACKLIGHT_PIN, HIGH);
    OnetimeDisplay("LCD", "Initialized");
}

inline void Display::OnetimeDisplay(char* pFirstRow,
                                    char* pSecondRow)
{
    lcd.setCursor(0,0);
    lcd.print(pFirstRow);
    lcd.setCursor(0,1);
    lcd.print(pSecondRow);
}

inline void Display::StatusDisplay()
{
    if ((millis() - lastDrawTime) < 1000)
    {
        return;
    }
    lastDrawTime = millis();

    // Do LCD display stuff
    lcd.setCursor(0,0);
    lcd.print(F("T:"));
    lcd.print(BridgeGetFloat("temperature"), 1);
    if (BridgeGetBool("lcdOverride"))
    {
        lcd.print (F(" OVERRIDE"));
    }
    else
    {
        lcd.setCursor(12,0);
        lcd.print(F("    "));
        lcd.setCursor(6,0);
        lcd.print(F(" H:"));
        lcd.print(BridgeGetFloat("humidity"), 0);
        lcd.print(F("%"));
    }
    lcd.setCursor(0,1);
    lcd.print(F("set:"));
    lcd.print(BridgeGetFloat("heatSetPoint"), 1);
    lcd.print(F("-"));
    lcd.print(BridgeGetFloat("coolSetPoint"), 1);

    unsigned long pythonUpdateMillis = BridgeGetULong("pythonUpdateTime");
    if (lastPythonUpdateMillis != pythonUpdateMillis)
    {
        if (twiddle == 'X')
        {
            twiddle = '+';
        }
        else
        {
            twiddle = 'X';
        }
        lcd.setCursor(15,1);
        lcd.print(twiddle);
    }
    else
    {
        if ((millis() - lastPythonUpdateMillis) > 40l * 1000l)
        {
            // It's been a long time since we heard from the python script
            lcd.setCursor(15,1);
            lcd.print("?");
        }
    }
    lastPythonUpdateMillis = pythonUpdateMillis;
}

inline void Display::FastUpdate()
{
    const unsigned long ONTIME_MS = 10 * 1000;
    const unsigned long DIMTIME_MS = 2 * 1000;
    const unsigned long BRIGHT = 255;
    const unsigned long DIM = 96;
    unsigned long backlight_timer = millis() - lastButtonPressTime;
    if (backlight_timer < ONTIME_MS)
    {
        gammaWrite(LCD_BACKLIGHT_PIN, BRIGHT);
    }
    else
    {
        backlight_timer -= ONTIME_MS;
        if (backlight_timer < DIMTIME_MS)
        {
            gammaWrite(LCD_BACKLIGHT_PIN, BRIGHT - ((backlight_timer * (BRIGHT-DIM))/DIMTIME_MS));
        }
        else
        {
            gammaWrite(LCD_BACKLIGHT_PIN, DIM);
        }
    }
}

inline int Display::GetButton()
{
    int keypress;
    keypress = analogRead(LCD_BUTTONS_PIN);
    int button = LCD_BUTTON_NO_BUTTON;
    if (keypress < 60)
    {
        button = LCD_BUTTON_RIGHT;
    }
    else if (keypress < 200)
    {
        button = LCD_BUTTON_UP;
    }
    else if (keypress < 400)
    {
        button = LCD_BUTTON_DOWN;
    }
    else if (keypress < 600)
    {
        button = LCD_BUTTON_LEFT;
    }
    else if (keypress < 800)
    {
        button = LCD_BUTTON_SELECT;
    }
    else
    {
        button = LCD_BUTTON_NO_BUTTON;
    }
    
    // Only send each button press once.
    if (lastButton == button)
    {
        return LCD_BUTTON_NO_BUTTON;
    }

    // we have a button press. force drawing.
    lastDrawTime = 0;
    lastButtonPressTime = millis();
    
    lastButton = button;
    return button;
}

#endif // INCLUDE GUARD