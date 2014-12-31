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

// Listen on default port 5555, the webserver on the Yún
// will forward there all the HTTP requests for us.
YunServer server;

#define DHTPIN 10

DHT dht(DHTPIN, DHT22);

float setPoint = 72.0;
float hysteresis = 1.0;
float recentTemperature = 72.0;

// The amount of time since the last temperature update.
unsigned long lastUpdateTime = 0;

void setup() 
{
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
  
  // restart this timer, now that the arduino is up.
  lastUpdateTime = millis();
}

void loop() 
{
  // Get clients coming from server
  YunClient client = server.accept();

  // There is a new client?
  if (client) {
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
  
  delay(50); // Poll every 50ms
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
  recentTemperature = dht.readTemperature(true);
  Bridge.put("temperature",String(recentTemperature));

  unsigned long uptime_ms = millis();
  Bridge.put("uptime_ms", String(uptime_ms));

  float humidity = dht.readHumidity();
  Bridge.put("humidity", String(humidity));

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
}

