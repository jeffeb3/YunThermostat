<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>Smart Temperature Sensor</title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!--External source-->
        <link rel="stylesheet" href="javascript/jquery-mobile/jquery.mobile.css">
        <script src="javascript/jquery/jquery.js"></script>
        <script src="javascript/jquery-mobile/jquery.mobile.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.time.js"></script>
        <script src="javascript/jquery-flot/jquery.flot.resize.js"></script>
        <!--Local source-->
        <script src="javascript/updater.js"></script>
        <link rel="stylesheet" href="static/arduino.css">

    </head>
    <body>

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

    </body>
</html>
