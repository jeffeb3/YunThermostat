
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
    
    float GetPrevHeatSetPoint() const
    {
        return prevHeatSetPoint;
    }

    float GetPrevCoolSetPoint() const
    {
        return prevCoolSetPoint;
    }
    
private:
    // Listen on default port 5555, the webserver on the Yun
    // will forward there all the HTTP requests for us.
    YunServer server;
    
    // time since the last read
    unsigned long lastReadTimeMillis;
    
    float prevHeatSetPoint;
    float prevCoolSetPoint;
    
    void Process(YunClient& client);
    void Read(YunClient& client);
    void Command(YunClient& client);
    void Heartbeat(YunClient& client);
};

Web::Web() :
    prevHeatSetPoint(HEAT_TEMP_DETACHED),
    prevCoolSetPoint(COOL_TEMP_DETACHED)
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
    
    if (command == "command") 
    {
        Command(client);
    }
    else if (command == "heartbeat") 
    {
        Heartbeat(client);
    }
    else
    {
        client.print(F("invalid REST command: '"));
        client.print(command);
        client.println(F("'"));
    }
}

void Web::Command(YunClient& client) 
{
    // Read desired state
    float heatSetPoint = client.parseFloat();
    float coolSetPoint = client.parseFloat();
  
    if ((heatSetPoint != prevHeatSetPoint) ||
        (coolSetPoint != prevCoolSetPoint))
    {
        prevHeatSetPoint = heatSetPoint;
        Bridge.put("heatSetPoint",String(heatSetPoint));
        prevCoolSetPoint = coolSetPoint;
        Bridge.put("coolSetPoint",String(coolSetPoint));
        Bridge.put("lcdOverride", "false");
    }
  
    // Send feedback to client
    client.print(F("The setPoint range is "));
    client.print(BridgeGetFloat("heatSetPoint"));
    client.print(F(" ... "));
    client.println(BridgeGetFloat("coolSetPoint"));
}

void Web::Heartbeat(YunClient& client)
{
    // put the amount of time since the last time this was called in a variable called lastUpdateTime
    Bridge.put("lastUpdateTime", String(millis() - BridgeGetULong("pythonUpdateTime")));
    Bridge.put("pythonUpdateTime", String(millis()));
    client.print(F("{\"uptime_ms\": "));
    client.print(BridgeGetULong("uptime_ms"));
    client.println(F("}"));
}

#endif // INCLUDE GUARD

