<!DOCTYPE html>
<!--[if lt IE 7]>      <html class="no-js lt-ie9 lt-ie8 lt-ie7"> <![endif]-->
<!--[if IE 7]>         <html class="no-js lt-ie9 lt-ie8"> <![endif]-->
<!--[if IE 8]>         <html class="no-js lt-ie9"> <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js"> <!--<![endif]-->
    <head>
        <meta charset="utf-8">
        <!--<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">-->
        <title>Smart Temperature Sensor</title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="javascript/jquery-mobile/jquery.mobile.css">

        <style>
            .plot-placeholder
            {
                width : 90%;
                height : 250px;
                text-align : center;
                margin : 0 auto;
            }
        </style>
        
        <!--[if lt IE 9]>
            <script src="//html5shiv.googlecode.com/svn/trunk/html5.js"></script>
            <script>window.html5 || document.write('<script src="js/vendor/html5shiv.js"><\/script>')</script>
        <![endif]-->
        
    </head>
    <body>
        <!--[if lt IE 7]>
            <p class="browsehappy">You are using an <strong>outdated</strong> browser. Please <a href="http://browsehappy.com/">upgrade your browser</a> to improve your experience.</p>
        <![endif]-->

        <!-- Start web page layout -->
        
        <div data-role="page" id="ContentsPage" data-theme="b">
            <div data-role="header">
                <a href="#ContentsPage" class="ui-btn ui-icon-home ui-btn-icon-left ui-btn-icon-notext">Home</a>
                <h1>Thermostat at {{ipaddress}}</h1>
            </div>
            <div data-role="main" class="ui-content">
                <h3 class="status">Connecting...</h3>
                <div data-role="collapsible">
                    <h1>Temperature: <span id="temperature">0</span> <span id="symbol"> &degF</span> Humidity: <span id="humidity">0</span>%</h1>
                    <div id="tempPlaceholder" class="plot-placeholder ui-body-inherit"></div>
                </div>
                <div data-role="collapsible">
                    <h1>Uptime: <span id="uptime_number">0</span></h1>
                    <div id="uptimePlaceholder" class="plot-placeholder"></div>
                </div>
            </div>
            <div data-role="footer"><h1></h1></div>
        </div>
        
        
        <!-- Start scripts -->
        <script src="javascript/jquery/jquery.min.js"></script>
        <script src="javascript/jquery-mobile/jquery.mobile.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.time.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.resize.js"></script>
        <script>
            $(document).ready(function()
            {
                // This is to debug problems with the javascript.
                window.onerror = function(msg, url, linenumber)
                {
                    alert('Error message: '+msg+'\nURL: '+url+'\nLine Number: '+linenumber);
                    return true;
                }
                
                var xIndex = 0;

                // this double curly braces is a keyword for bottle to replace with text from python.
                var tempPlotData = [ { label: "Temp(&degF)", data: {{tempPlotData}} }, { label: "Humidity(%)", data: {{humidPlotData}}, yaxis: 2 } ];
                var uptimePlotData = [ { label: "Arduino", data: [] }, { label: "Linux", data: [] } ];

                var lastMeasureTime = 0.0;

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
                
                function clipData(data, maxNum = 1000)
                {
                    if (data.length > maxNum)
                    {
                        data = data.slice(maxNum);
                    }
                }
                
                function updateMeasurement(data)
                {
                    if (data.time != lastMeasureTime)
                    {
                        lastMeasureTime = data.time
                        // Update the plot
                        tempPlotData[0].data.push([data.time,data.temperature]);
                        tempPlotData[1].data.push([data.time,data.humidity]);
                        uptimePlotData[0].data.push([data.time,data.uptime_ms]);
                        uptimePlotData[1].data.push([data.time,data.py_uptime_ms]);
    
                        clipData(tempPlotData[0].data);
                        clipData(tempPlotData[1].data);
                        clipData(uptimePlotData[0].data);
                        clipData(uptimePlotData[1].data);
                        
                        tempPlot.setData(tempPlotData);
                        tempPlot.setupGrid();
                        tempPlot.draw();
                        
                        uptimePlot.setData(uptimePlotData);
                        uptimePlot.setupGrid();
                        uptimePlot.draw();
                        
                        // Update the UI.
                        $('#temperature').text(data.temperature.toPrecision(3));
                        $('#humidity').text(data.humidity.toPrecision(3));
                        $('#uptime_number').text('Arduino: ' + msToText(data.uptime_ms) + ' Linux: ' + msToText(data.py_uptime_ms));
                    }
                }

                // Start with main controls hidden until connected.
                $('#main').hide();
        
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
                    $('#main').show();
                };
                server.onerror = function(e)
                {      
                    // Hide controls and show connecting status.
                    $('#main').hide();
                    $('.status h3').text('Connecting...');
                    $('.status').show();
                };

                function humidityPercent(humidity, axis)
                {
                    return humidity.toFixed(axis.tickDecimals) + "%%";
                }
                
                function temperatureDeg(temperature, axis)
                {
                    return temperature.toFixed(axis.tickDecimals) + "F";
                }
                
                var tempPlot = $.plot("#tempPlaceholder", [ tempPlotData ], 
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
                    yaxis:
                    [
                    {
                        tickFormatter : temperatureDeg,
                        tickDecimals : 0
                    },
                    {
                        alignTicksWithAxis : null,
                        position : "left",
                        tickDecimals : 0,
                        tickFormatter : humidityPercent
                    }
                    ],
                    xaxis:
                    {
                        mode: "time",
                    }
                });

                var uptimePlot = $.plot("#uptimePlaceholder", [ uptimePlotData ], 
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
                    }
                });

            });

      </script>
    </body>
</html>
