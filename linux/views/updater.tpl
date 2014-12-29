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
    var tempPlotData =
    [
        {
            label: "Temp(&degF)",
            data: {{tempPlotData}}
        },
        {
            label: "Humidity(%)",
            data: {{humidPlotData}},
            yaxis: 2
        },
        {
            label: "Heat On",
            data: {{heatPlotData}},
            points: { show : false },
            yaxis: 3
        }
    ];
    
    var healthPlotData =
    [
        {
            label: "Update Time",
            data: {{updateTimePlotData}}
        }
    ];
    
    var tempPlot = null;
    var healthPlot = null;

    // *************** Initial GUI updates
    $("#heatStatus").hide();

    // *************** Initialize the plots
    
    tempPlot = $.plot(
        $("#tempPlaceholder"),
        tempPlotData,
        { 
            xaxes: [ { mode: 'time' } ],
            yaxes: [
            {
                autoscaleMargin : 1.1,
                tickFormatter : temperatureDeg,
                //tickDecimals : 2
            },
            {
                alignTicksWithAxis: 1,
                tickFormatter : humidityPercent,
                //tickDecimals : 2,
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
                mode: "time",
            },
            yaxis:
            {
                tickFormatter: msToText,
                min : 0
            },
            legend:
            {
                noColumns : 2,
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
            tempPlotData[0].data.push([data.time,data.temperature]);
            tempPlotData[1].data.push([data.time,data.humidity]);
            tempPlotData[2].data.push([data.time,data.heat]);
            healthPlotData[0].data.push([data.time,data.lastUpdateTime]);
                        
            tempPlot.setData(tempPlotData);
            tempPlot.setupGrid();
            tempPlot.draw();
            
            healthPlot.setData(healthPlotData);
            healthPlot.setupGrid();
            healthPlot.draw();
            
            // Update the UI.
            $('#temperature').text(data.temperature.toPrecision(3));
            $('#humidity').text(data.humidity.toPrecision(3));
            $('#uptime_number').text('Arduino: ' + msToText(data.uptime_ms) + ' Linux: ' + msToText(data.py_uptime_ms));
            var now = new Date(data.time + {{timezone}});
            $('#now').text(now.toLocaleString());
            if (data.heat == 0)
            {
                $("#heatStatus").hide(1000);
            }
            else
            {
                $("#heatStatus").show(1000);
            }
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
    return temperature.toFixed(axis.tickDecimals) + "F";
}

