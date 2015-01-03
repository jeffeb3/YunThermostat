//! collection of scripts to dynamically update things on a web page for the
//! arduino thermostat project.
//! @note This file is a SimpleTemplate file (http://bottlepy.org/docs/dev/stpl.html)
//! It is meant to be used with bottle, and won't load on it's own.

// *************** don't do this stuff until the page completely loads
$(document).ready(function()
{    

    // *************** This is to debug problems with the javascript.
    window.onerror = function(msg, url, linenumber)
    {
        alert('Error message: '+msg+'\nURL: '+url+'\nLine Number: '+linenumber);
        return true;
    }
    
    // *************** globals
    var temperaturePlotData =
    [
        {
            label: "Temp(&degF)",
            data: {{temperatureHistory}}
        },
        {
            label: "Humidity(%)",
            data: {{humidityHistory}},
            yaxis: 2
        },
        {
            label: "Heat On",
            data: {{heatHistory}},
            points: { show : false },
            yaxis: 3
        }
    ];
    
    var healthPlotData =
    [
        {
            label: "Update Time",
            data: {{updateTimeHistory}}
        },
        {
            label: "Flappy Ping",
            data: {{flappyPingHistory}},
            yaxis: 2
        },
        {
            label: "Phone Ping",
            data: {{phonePingHistory}},
            yaxis: 2
        }
    ];
    
    var tempPlot = null;
    var healthPlot = null;

    // *************** Initial GUI updates
    $("#heatStatus").hide();
    $("#coolStatus").hide();

    // *************** Initialize the plots
    
    tempPlot = $.plot(
        $("#tempPlaceholder"),
        temperaturePlotData,
        { 
            xaxes: [
                    {
                        ticks: 4,
                        mode: 'time'
                    }
                    ],
            yaxes: [
            {
                autoscaleMargin : 1.1,
                tickFormatter : temperatureDeg,
            },
            {
                alignTicksWithAxis: 1,
                tickFormatter : humidityPercent,
                position: "right"
            },
            {
                show: false,
                min: -0.1,
                max: 1.1
            }],
            series: {
                shadowSize: 0, // Drawing is faster without shadows
                lines: { show: true }
            },
            legend:
            {
                noColumns : 4,
                container : $("#tempLegend")
            }
        });

    healthPlot = $.plot(
        $("#healthPlaceholder"),
        healthPlotData, 
        {
            series:
            {
                shadowSize: 0	// Drawing is faster without shadows
            },
            lines:
            {
                show: true
            },
            points:
            {
                show: true
            },
            xaxis:
            {
                ticks: 4,
                mode: "time",
            },
            yaxes: [
            {
                tickFormatter: msToText,
                min : 0
            },
            {
                alignTicksWithAxis: 1,
                position: "right",
                ticks: [[0,"Fail"], [1,"OK"]],
                min: -0.1,
                max: 1.1
            }],
            legend:
            {
                noColumns : 3,
                container : $("#healthLegend")
            }
        });

    var lastMeasureTime = 0.0;
    function updateMeasurement(data)
    {
        if (data.time != lastMeasureTime)
        {
            lastMeasureTime = data.time
            // Update the plots
            temperaturePlotData[0].data.push([data.time - {{timezone}},data.temperature]);
            temperaturePlotData[1].data.push([data.time - {{timezone}},data.humidity]);
            temperaturePlotData[2].data.push([data.time - {{timezone}},data.heat]);
            healthPlotData[0].data.push([data.time - {{timezone}},data.lastUpdateTime]);
            healthPlotData[1].data.push([data.time - {{timezone}},data.flappy_ping]);
            healthPlotData[2].data.push([data.time - {{timezone}},data.phone_ping]);
                        
            tempPlot.setData(temperaturePlotData);
            tempPlot.setupGrid();
            tempPlot.draw();
            
            healthPlot.setData(healthPlotData);
            healthPlot.setupGrid();
            healthPlot.draw();
            
            // Update the UI.
            $('#temperature').text(data.temperature.toPrecision(3));
            $('#humidity').text(data.humidity.toPrecision(3));
            $('#uptime_number').text('Arduino: ' + msToText(data.uptime_ms) + ' Linux: ' + msToText(data.py_uptime_ms));
            var now = new Date(data.time);
            $('#now').text(now.toLocaleString());
            if (data.heat == 0)
            {
                $("#heatStatus").hide(1000);
            }
            else
            {
                $("#heatStatus").show(1000);
            }
            if (data.cool == 0)
            {
                $("#coolStatus").hide(1000);
            }
            else
            {
                $("#coolStatus").show(1000);
            }
            $(".heatSetPoint").text(data.setPoint.toPrecision(3));
            $(".coolSetPoint").text(data.setPoint.toPrecision(3)); // TODO, make a different set point for cooling.
        }
    }
    
    // Create server sent event connection.
    var server = new EventSource('/measurements');
    server.onmessage = function(e)
    {
        // Update measurement value.
        var data = JSON.parse(e.data);
        updateMeasurement(data);
    };
    server.onopen = function(e)
    {
        // Hide connecting status and show controls.
        $('.disconnected').hide();
        $('.connected').show();
        $('#now').text('Now');
    };
    server.onerror = function(e)
    {      
        // Hide controls and show connecting status.
        $('.status h3').text('Connecting...');
        $('.disconnected').show();
        $('.connected').hide();
    };
});

function msToText(milliseconds)
{
    var seconds = milliseconds / 1000.0;
    var minutes = Math.floor(seconds / 60.0);
    seconds -= minutes * 60.0;
    var hours = Math.floor(minutes / 60.0);
    minutes -= hours * 60.0;
    var days = Math.floor(hours / 24.0);
    hours -= days * 24.0;

    var text = seconds.toPrecision(3).toString();
    if (minutes > 0 || hours > 0 || days > 0)
    {
        text = hours.toString() + ':' + minutes.toString() + ':' + text;
    }
    if (days > 0)
    {
        text = days.toString() + 'd ' + text;
    }
    return text;
}

function humidityPercent(humidity, axis)
{
    return humidity.toFixed(axis.tickDecimals) + "%";
}

function temperatureDeg(temperature, axis)
{
    return temperature.toFixed(axis.tickDecimals) + "&degF";
}

