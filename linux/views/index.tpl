<!DOCTYPE html>
<!--[if lt IE 7]>      <html class="no-js lt-ie9 lt-ie8 lt-ie7"> <![endif]-->
<!--[if IE 7]>         <html class="no-js lt-ie9 lt-ie8"> <![endif]-->
<!--[if IE 8]>         <html class="no-js lt-ie9"> <![endif]-->
<!--[if gt IE 8]><!--> <html class="no-js"> <!--<![endif]-->
    <head>
        <meta charset="utf-8">
        <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
        <title>Smart Temperature Sensor</title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">

        <link href="//netdna.bootstrapcdn.com/bootstrap/3.1.1/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body {
              padding-top: 50px;
              padding-bottom: 20px;
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
        <div class="container">
            <div class="jumbotron">
                <h1>Smart Temperature Sensor</h1>
            </div>
            <div class="row" id="status">
                <div class="col-md-12">
                    <h3>Connecting...</h3>
                </div>
            </div>
            <div class="row" id="main">
                <div class="col-md-2">
                    <label>Temperature:</label>
                    <h3>
                        <span id="measurement">0</span> <span id="symbol">deg F</span>
                    </h3>
                </div>
            </div>
            <div class="row" id="plot">
                <div id="placeholder" class="plot-placeholder" style="width: 100%;height:400px; text-align: center; margin:0 auto;"></div>
            </div>
        </div>
        <script src="//ajax.googleapis.com/ajax/libs/jquery/1.11.0/jquery.min.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.time.js"></script>
        <!--<script src="//netdna.bootstrapcdn.com/bootstrap/3.1.1/js/bootstrap.min.js"></script>-->
        <!--<script src="http://cdn.bobcravens.com/wp-content/uploads/2011/01/jquery.flot.js"></script>-->
        <script>
            $(document).ready(function()
            {
                window.onerror = function(msg, url, linenumber)
                {
                    alert('Error message: '+msg+'\nURL: '+url+'\nLine Number: '+linenumber);
                    return true;
                }
                
                var xIndex = 0;
                var plotData = {{plotData}};

                var lastMeasure = 0.0;

                function updateMeasurement(data)
                {
                    // Update the plot
                    plotData[0].push([data.time,data.temperature]);
                    // clip to 10 points
                    if (plotData[0].length > 600)
                    {
                        plotData[0] = plotData[0].slice(1);
                    }
                    
                    plot.setData(plotData);
                    plot.setupGrid();
                    plot.draw();
                    
                    // Update the UI.
                    $('#measurement').text(data.temperature.toPrecision(5));
                }

                function setStatus(status)
                {
                    if (status)
                    {
                        // Update status text and show the state area.
                        $('#status h3').text(status);
                        $('#status').show();
                    }
                    else
                    {
                        // Hide status area if null/empty status.
                        $('#status').hide();
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
                    lastMeasure = data.temperature;
                };
                server.onopen = function(e)
                {
                    // Hide connecting status and show controls.
                    $('#status').hide();
                    $('#main').show();
                };
                server.onerror = function(e)
                {      
                    // Hide controls and show connecting status.
                    $('#main').hide();
                    $('#status h3').text('Connecting...');
                    $('#status').show();
                };

                var plot = $.plot("#placeholder", [ plotData ], 
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
                    {
                        min: 67,
                        max: 73
                    },
                    xaxis:
                    {
                        mode: "time",
                    }
                });

            });

      </script>
    </body>
</html>
