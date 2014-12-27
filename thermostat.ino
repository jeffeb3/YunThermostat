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
  float temp = dht.readTemperature(true);
  Bridge.put("temperature",String(temp));
  float humidity = dht.readHumidity();
  Bridge.put("humidity", String(humidity));
  // Send feedback to client
  client.print(F("{\n"));
  client.print(F("  \"uptime_ms\" : "));
  unsigned long uptime_ms = millis();
  client.print(uptime_ms);
  Bridge.put("uptime_ms", String(uptime_ms));
  client.print(F(",\n"));
  client.print(F("  \"temperature\" : "));
  client.print(temp);
  client.print(F(",\n"));
  client.print(F("  \"heat\" : "));
  client.print(digitalRead(13));
  client.print(F(",\n"));
  client.print(F("  \"humidity\": "));
  client.print(humidity);
  client.println(F("\n}"));
}

void heatCommand(YunClient client) 
{
  int on;
  
  // Read desired state
  on = client.parseInt();

  digitalWrite(13, on);

  // Send feedback to client
  client.print(F("The heat is ... "));
  client.println((on == 1 ? F("On") : F("Off")));
  Bridge.put("heat",String(on));
}

