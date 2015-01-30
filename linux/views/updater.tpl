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
            data: {{temperatureHistory}},
            color: 'yellow'
        },
        {
            label: "OutsideTemp(&degF)",
            data: {{outsideTempHistory}},
            color: 'lightblue',
            yaxis: 2
        },
        {
            label: "Heat On",
            data: {{heatHistory}},
            points: { show : false },
            color: 'red',
            yaxis: 3
        },
        {
            label: "A/C On",
            data: {{coolHistory}},
            points: { show : false },
            color: 'blue',
            yaxis: 3
        }
    ];
    
    var logicPlotData =
    [
        {
            label: "Heat Temp(&degF)",
            points: { show : false },
            color: 'red',
            data: {{setHeatHistory}}
        },
        {
            label: "Cool Temp(&degF)",
            points: { show : false },
            color: 'blue',
            data: {{setCoolHistory}}
        },
        {
            label: "Home",
            data: {{homeHistory}},
            points: { show : false },
            color: 'lightgreen',
            yaxis: 2
        },
        {
            label: "Sleeping",
            data: {{sleepHistory}},
            color: 'lightblue',
            points: { show : false },
            yaxis: 2
        }
    ];
    
    var healthPlotData =
    [
        {
            label: "Update Time",
            points: { show : false },
            data: {{updateTimeHistory}}
        },
        {
            label: "Free Memory %",
            data: {{memHistory}},
            points: { show : false },
            yaxis: 2
        }
    ];
    
    var tempPlot = null;
    var logicPlot = null;
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
                        mode: 'time',
                    }
                    ],
            yaxes: [
            {
                tickFormatter : temperatureDeg,
                tickDecimals: 1
            },
            {
                tickFormatter : temperatureDeg,
                tickDecimals: 1,
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

    logicPlot = $.plot(
        $("#logicPlaceholder"),
        logicPlotData,
        { 
            xaxes: [
                    {
                        ticks: 4,
                        mode: 'time',
                    }
                    ],
            yaxes: [
            {
                tickFormatter : temperatureDeg,
                tickDecimals: 1
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
                container : $("#logicLegend")
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
                tickFormatter : percFormat,
                position: "right"
            }],
            legend:
            {
                noColumns : 2,
                container : $("#healthLegend")
            }
        });
    
    var plots = [tempPlot, logicPlot, healthPlot];

    var lastMeasureTime = 0.0;
    function updateMeasurement(data)
    {
        if (data.time != lastMeasureTime)
        {
            lastMeasureTime = data.time
            // Update the plots
            temperaturePlotData[0].data.push([data.time - {{timezone}},data.temperature]);
            if (data.outside_temp_updated)
            {
                temperaturePlotData[1].data.push([data.time - {{timezone}},data.outside_temp]);
            }
            temperaturePlotData[2].data.push([data.time - {{timezone}},data.heat]);
            temperaturePlotData[3].data.push([data.time - {{timezone}},data.cool]);

            logicPlotData[0].data.push([data.time - {{timezone}},data.heatSetPoint]);
            logicPlotData[1].data.push([data.time - {{timezone}},data.coolSetPoint]);
            logicPlotData[2].data.push([data.time - {{timezone}},1.0 - data.away]);
            logicPlotData[3].data.push([data.time - {{timezone}},data.sleeping]);
            
            healthPlotData[0].data.push([data.time - {{timezone}},data.lastUpdateTime]);
            healthPlotData[1].data.push([data.time - {{timezone}},data.linux_free_mem_perc]);

            tempCopy = [temperaturePlotData[0], temperaturePlotData[1]];
            if ($("#doHeat").is(":checked"))
            {
                tempCopy.push(temperaturePlotData[2]);
            }
            if ($("#doCool").is(":checked"))
            {
                tempCopy.push(temperaturePlotData[3]);
            }

            tempPlot.setData(tempCopy);
            tempPlot.setupGrid();
            tempPlot.draw();
            
            tempCopy = []
            if ($("#doHeat").is(":checked"))
            {
                tempCopy.push(logicPlotData[0]);
            }
            if ($("#doCool").is(":checked"))
            {
                tempCopy.push(logicPlotData[1]);
            }
            tempCopy.push(logicPlotData[2]);
            tempCopy.push(logicPlotData[3]);
            

            logicPlot.setData(tempCopy);
            logicPlot.setupGrid();
            logicPlot.draw();

            healthPlot.setData(healthPlotData);
            healthPlot.setupGrid();
            healthPlot.draw();
            
            // Update the UI.
            $('#temperature').text(data.temperature.toPrecision(3));
            $('#outsideTemperature').text(data.outside_temp.toPrecision(3));
            $('#humidity').text(data.humidity.toPrecision(3));
            $('#uptime_number').text('Arduino: ' + msToText(data.uptime_ms) + ' Linux: ' + msToText(data.linux_uptime_ms) + ' Python: ' + msToText(data.py_uptime_ms));
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
            $(".heatSetPoint").text(data.heatSetPoint.toPrecision(3));
            $(".coolSetPoint").text(data.coolSetPoint.toPrecision(3)); // TODO, make a different set point for cooling.
            $("#heatOverrideEnable").prop('checked', data.lcdOverride);
            $("#coolOverrideEnable").prop('checked', data.lcdOverride);
        }
    }

    $("#plotTimeAll").click(function() {
        $(plots).each(function() {
            this.getOptions().xaxes[0].min = null;
            this.setupGrid();
            this.draw();
        })
    });
    
    $("#plotTimeDay").click(function() {
        $(plots).each(function() {
            this.getOptions().xaxes[0].min = Date.now() - 24 * 60 * 60 * 1000 - {{timezone}};
            this.setupGrid();
            this.draw();
        })
    });
    
    $("#plotTimeHour").click(function() {
        $(plots).each(function() {
            this.getOptions().xaxes[0].min = Date.now() - 60 * 60 * 1000 - {{timezone}};
            this.setupGrid();
            this.draw();
        })
    });
    
    $("#plotTimeMinutes").click(function() {
        $(plots).each(function() {
            this.getOptions().xaxes[0].min = Date.now() - 10 * 60 * 1000 - {{timezone}};
            this.setupGrid();
            this.draw();
        })
    });
    
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
    
    // Create server sent event connection for the logger.
    var log_server = new EventSource('/logs');

    function writeLog(data)
    {
        $("#appendLogs").append(data);
        $("#logTable").table("refresh");
    };

    log_server.onmessage = function(e)
    {
        // Update measurement value.
        writeLog(e.data);
    };

    log_server.onopen = function(e)
    {
        writeLog('<tr>' +
                 '<th class="logLevelINFO">INFO</th>' +
                 '<td class="logMessage">Connected</td>' +
                 '<td class="logTime"></td>' +
                 '<td class="logName"></td>' +
                 '<td class="logFile"></td>' +
                 '</tr>');
    };

    log_server.onerror = function(e)
    {
        writeLog('<tr>' +
                 '<th class="logLevelINFO">INFO</th>' +
                 '<td class="logMessage">Disconnected</td>' +
                 '<td class="logTime"></td>' +
                 '<td class="logName"></td>' +
                 '<td class="logFile"></td>' +
                 '</tr>');
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
        if (seconds < 10)
        {
            text = "0" + text;
        }
        text = minutes.toString() + ':' + text;
        if (minutes < 10)
        {
            text = "0" + text;
        }
        text = hours.toString() + ':' + text;
    }
    if (days > 0)
    {
        text = days.toString() + 'd ' + text;
    }
    return text;
}

function percFormat(value, axis)
{
    return value.toFixed(axis.tickDecimals) + "%";
}

function temperatureDeg(temperature, axis)
{
    return temperature.toFixed(axis.tickDecimals) + "&degF";
}

