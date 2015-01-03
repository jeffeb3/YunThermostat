// This sketch is the physical connection to the DHT22 temperature/humidity sensor and some output relays via the REST API
//
//
// To read the sensor data:
// 10.0.2.208/arduino/sensors
//
// This will return a JSON object:
// {
//   temperature : 76.23 // farenheit
//   humidity : 5 // percent
// }
//
// To control the output:
// 10.0.2.208/arduino/heat/1
// 10.0.2.208/arduino/heat/0

#include <Bridge.h>
#include <YunServer.h>
#include <YunClient.h>
#include <DHT.h>
#include <LiquidCrystal.h>


// Listen on default port 5555, the webserver on the Yún
// will forward there all the HTTP requests for us.
YunServer server;

// Set pins used in LCD display
LiquidCrystal lcd(8, 9, 4, 5, 6, 7);
#define DHTPIN 10

DHT dht(DHTPIN, DHT22);

//set initial settings
float setPoint = 72.0;
float hysteresis = 0.4;
float recentTemperature = 72.0;
float humidity = 10.0;
const float temperatureLPF = 0.5;
const float humidityLFP = 0.5;
int setOverride = 0;

// The amount of time since the last temperature update.
unsigned long lastUpdateTime = 0;

void setup() 
{
  // set up the LCD's number of columns and rows:
  lcd.begin(16, 2);
  lcd.setCursor(0,0);
  lcd.print("Waiting for the");
  lcd.setCursor(0,1);
  lcd.print("Bridge");

  // Bridge startup, make the L13 LED go on, then initialize, then off.
  pinMode(13, OUTPUT);
  digitalWrite(13, HIGH);
  Bridge.begin();
  digitalWrite(13, LOW);
  
  // Use the pins to power the DHT. It's easier than using jumpers
  // Connect the DHT22 (RHT03) in D9-D12. 
  // Rotate the sensor so you can see the grill and the arduino pins at the same time.
  // PINOUT: Vcc, Signal, NC, Gnd when you can see the grill.
  pinMode(9,OUTPUT);
  pinMode(12,OUTPUT);
  digitalWrite(9,HIGH);
  digitalWrite(12,LOW);

  // Listen for incoming connection only from localhost
  // (no one from the external network could connect)
  server.listenOnLocalhost();
  server.begin();
  
  lcd.setCursor(0,0);
  lcd.print("                ");
  lcd.setCursor(0,1);
  lcd.print("                ");

  // restart this timer, now that the arduino is up.
  lastUpdateTime = millis();
  
}

void loop() 
{
  // Do LCD display stuff
  lcd.setCursor(0,0);
  lcd.print("T:");

  recentTemperature = smooth(dht.readTemperature(true), temperatureLPF, recentTemperature);
  if (isnan(recentTemperature))
  {
    recentTemperature = 32.0;
  }
  Bridge.put("temperature",String(recentTemperature));
  humidity = smooth(dht.readHumidity(), humidityLFP, humidity);
  Bridge.put("humidity", String(humidity));
  
  lcd.print(recentTemperature, 1);
  lcd.print(" set:");
  lcd.print(setPoint, 1);
  lcd.setCursor(0,1);
  lcd.print("H:");
  lcd.print(humidity, 1);
  
  // Manual override with buttons
  int keypress;
  keypress = analogRead (0);
  if (keypress < 60) {
  }
  else if (keypress < 200) {
    setPoint = setPoint + 1;
    setOverride = 1;
    lcd.setCursor(8,1);
    lcd.print ("OVER");
  }
  else if (keypress < 400){
    setPoint = setPoint - 1;
    setOverride = 1;      
    lcd.setCursor(8,1);
    lcd.print ("OVER");
  }
  else if (keypress < 600){
  }
  else if (keypress < 800){
    // need to get setPoint from Linux here
    setOverride = 0;        
    lcd.setCursor(8,1);
    lcd.print ("    ");
  }

  
  // Get clients coming from server
  YunClient client = server.accept();

  // There is a new client?
  if (client)
  {
    // Process request
    process(client);

    // Close connection and free resources.
    client.stop();
  }

  // if the temperature is more than the hysteresis above the set point.
  if (recentTemperature - setPoint > hysteresis)
  {
    // turn it off
    digitalWrite(13, LOW);
  }
  // else if the temperature is less than the hysteresis below the set point,
  else if (setPoint - recentTemperature > hysteresis)
  {
    // turn it on
    digitalWrite(13, HIGH);
  }
  
  if ((millis() - lastUpdateTime) > 180 * 1000)
  {
    // It's been over three minutes since we heard from the python script
    lcd.setCursor(15,1);
    lcd.print("?");
  }
  delay(2000); // Poll every 200ms
}

void process(YunClient client) 
{
  // read the command
  String command = client.readStringUntil('/');
  
  command.trim(); // remove trailing whitespace
  
  // is "sensors" command?
  if (command == "sensors") 
  {
    readSensors(client);
  }
  else if (command == "heat") 
  {
    heatCommand(client);
  }
  else
  {
    client.print(F("invalid REST command: '"));
    client.print(command);
    client.println(F("'"));
  }

}

void readSensors(YunClient client) 
{
  unsigned long uptime_ms = millis();
  Bridge.put("uptime_ms", String(uptime_ms));

  // Send feedback to client
  client.print(F("{\n"));
  client.print(F("  \"uptime_ms\" : "));
  client.print(uptime_ms);
  client.print(F(",\n"));
  client.print(F("  \"temperature\" : "));
  client.print(recentTemperature);
  client.print(F(",\n"));
  client.print(F("  \"humidity\": "));
  client.print(humidity);
  client.print(F(",\n"));
  client.print(F("  \"setPoint\" : "));
  client.print(setPoint);
  client.print(F(",\n"));
  client.print(F("  \"setOverride\" : "));
  client.print(setOverride);
  client.print(F(",\n"));
  client.print(F("  \"lastUpdateTime\" : "));
  client.print(millis() - lastUpdateTime);
  client.print(F(",\n"));
  client.print(F("  \"heat\" : "));
  client.print(digitalRead(13));
  client.print(F(",\n"));
  client.print(F("  \"cool\" : "));
  client.print(false);
  client.println(F("\n}"));

  // restart this timer
  lastUpdateTime = millis();

}

void heatCommand(YunClient client) 
{
  // Read desired state
  setPoint = client.parseFloat();

  // Send feedback to client
  client.print(F("The setPoint is ... "));
  client.println(setPoint);
  Bridge.put("setPoint",String(setPoint));
  lcd.setCursor(15,1);
  if (millis() % 60000 < 30000)
  {
    lcd.print("+");
  }
  else
  {
    lcd.print("X");
  }
}

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


