<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>Smart Temperature Sensor</title>
        <meta name="description" content="">
        <script src="javascript/jquery/jquery.js"></script>
        <script src="javascript/jquery-mobile/jquery.mobile.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.time.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.resize.js"></script>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="javascript/jquery-mobile/jquery.mobile.css">

        <style>
            .plot-placeholder
            {
                width : 100%;
                height : 250px;
                text-align : center;
                margin : 0 auto;
            }
            .plot-legend
            {
                padding-right: 10px;
            }
        </style>
        
    </head>
    <body>
        <!-- Start web page layout -->
        
        <div data-role="page" id="ContentsPage" data-theme="b">
            
            <div data-role="header">
                <a href="#ContentsPage" class="ui-btn ui-icon-home ui-btn-icon-left ui-btn-icon-notext">Home</a>
                <h1>{{ipaddress}}'s Control</h1>
            </div>
            
            <div data-role="main" class="ui-content">

                <h4>Last Update: <span id="now"></span></h4>
                
                <h3 class="status">Connecting...</h3>

                <h3 id="heatStatus" style="color:#FF4444">The Heat is ... ON!</h3>
                
                <div data-role="collapsible" data-collapsed="false">
                    <h1>T: <span id="temperature">?</span> &degF H: <span id="humidity">?</span>%</h1>
                    <div id="tempPlaceholder" class="plot-placeholder ui-body-inherit"></div>
                    <div id="tempLegend"      class="legend-placeholder ui-body-inherit"></div>
                </div>

                <div data-role="collapsible">
                    <h1>System Health</h1>
                    <h4>Uptime: <span id="uptime_number">?</span></h4>
                    <div id="healthPlaceholder" class="plot-placeholder"></div>
                    <div id="healthLegend"      class="legend-placeholder ui-body-inherit"></div>
                </div>

            </div>
            
            <div data-role="footer"><h1></h1></div>
            
        </div>

        <!-- Start scripts -->
        <script type="text/javascript">
    
            $(document).ready(function()
            {
                // This is to debug problems with the javascript.
                window.onerror = function(msg, url, linenumber)
                {
                    alert('Error message: '+msg+'\nURL: '+url+'\nLine Number: '+linenumber);
                    return true;
                }
            
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
                        label: "Arduino",
                        data: {{arduinoUptimePlotData}}
                    },
                    {
                        label: "Linux",
                        data: {{linuxUptimePlotData}}
                    }
                ];
            
                var tempPlot = $.plot(
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
            
                var healthPlot = $.plot(
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
                            tickFormatter: msToText
                        },
                        legend:
                        {
                            noColumns : 2,
                            container : $("#healthLegend")
                        }
                    });
            
                // hide this, initially
                $("#heatStatus").hide()
                
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
                        healthPlotData[0].data.push([data.time,data.uptime_ms]);
                        healthPlotData[1].data.push([data.time,data.py_uptime_ms]);
                                    
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
                    $('.status').hide();
                    $('#now').show();
                    $('#now').text('Now');
                };
                server.onerror = function(e)
                {      
                    // Hide controls and show connecting status.
                    $('.status h3').text('Connecting...');
                    $('.status').show();
                    $('#now').hide();
                };
            
                function msToText(milliseconds)
                {
                    var seconds = milliseconds / 1000.0;
                    var minutes = Math.floor(seconds / 60.0);
                    seconds -= minutes * 60.0;
                    var hours = Math.floor(minutes / 60.0);
                    minutes -= hours * 60.0;
                    var days = Math.floor(hours / 24.0);
                    hours -= days * 24.0;
                    
                    var text = hours.toString() + ':' + minutes.toString() + ':' + seconds.toPrecision(3).toString();
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
            
            });
        </script>
    </body>
</html>
