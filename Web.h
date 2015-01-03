
// This file contains the web interface to this script.
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

#ifndef THERMOSTAT_WEB_H_
#define THERMOSTAT_WEB_H_

#include <YunServer.h>
#include <YunClient.h>

class Web
{
public:
    Web();
    
    void Setup();
    
    void Update();
    
private:
    // Listen on default port 5555, the webserver on the Yun
    // will forward there all the HTTP requests for us.
    YunServer server;
    
    // time since the last read
    unsigned long lastReadTimeMillis;
    
    void Process(YunClient& client);
    void Read(YunClient& client);
    void Command(YunClient& client);
};

Web::Web()
{
}

void Web::Setup()
{
    // Listen for incoming tcp connections (port 5555) only from localhost. The
    // linino will forward connections from everyone else.
    server.listenOnLocalhost();
    server.begin();

    // restart this timer
    lastReadTimeMillis = millis();
}

void Web::Update()
{
    // Get clients coming from server
    YunClient client = server.accept();

    // There is a new client?
    if (client)
    {
        // Process request
        Process(client);

        // Close connection and free resources.
        client.stop();
    }
}


void Web::Process(YunClient& client) 
{
    // read the command
    String command = client.readStringUntil('/');
    
    command.trim(); // remove trailing whitespace
    
    // is "sensors" command?
    if (command == "sensors") 
    {
        Read(client);
    }
    else if (command == "heat") 
    {
        Command(client);
    }
    else
    {
        client.print(F("invalid REST command: '"));
        client.print(command);
        client.println(F("'"));
    }
}

void Web::Read(YunClient& client) 
{
    unsigned long uptime_ms = millis();
    Bridge.put("uptime_ms", String(uptime_ms));

    // Send feedback to client
    client.print(F("{\n"));
    client.print(F("  \"uptime_ms\" : "));
    client.print(uptime_ms);
    client.print(F(",\n"));
    client.print(F("  \"temperature\" : "));
    client.print(BridgeGetFloat("temperature"));
    client.print(F(",\n"));
    client.print(F("  \"humidity\": "));
    client.print(BridgeGetFloat("humidity"));
    client.print(F(",\n"));
    client.print(F("  \"setPoint\" : "));
    client.print(BridgeGetFloat("setPoint"));
    client.print(F(",\n"));
    client.print(F("  \"lcdOverride\" : "));
    client.print(BridgeGetBool("lcdOverride"));
    client.print(F(",\n"));
    client.print(F("  \"lastUpdateTime\" : "));
    client.print(millis() - lastReadTimeMillis);
    client.print(F(",\n"));
    client.print(F("  \"heat\" : "));
    client.print(digitalRead(13));
    client.print(F(",\n"));
    client.print(F("  \"cool\" : "));
    client.print(false);
    client.println(F("\n}"));
  
    // restart this timer
    lastReadTimeMillis = millis();
}

void Web::Command(YunClient& client) 
{
    // Read desired state
    int setPoint = client.parseFloat();
  
    // Send feedback to client
    client.print(F("The setPoint is ... "));
    client.println(setPoint);
    Bridge.put("setPoint",String(setPoint));
    Bridge.put("pytonUpdateTime", String(millis()));
}

#endif // INCLUDE GUARD

