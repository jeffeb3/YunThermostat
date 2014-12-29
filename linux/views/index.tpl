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
        <script src="javascript/forms.js"></script>
        <link rel="stylesheet" href="static/arduino.css">

    </head>
    <body>

        <div data-role="page" id="ContentsPage" data-theme="b">
            
            <div data-role="header">
                <a href="#ContentsPage" class="ui-btn ui-icon-home ui-btn-icon-left ui-btn-icon-notext">Home</a>
                <a href="#ConfigurePage" class="ui-btn ui-icon-gear ui-btn-icon-right ui-btn-icon-notext">Config</a>
                <h1>{{ipaddress}}'s Control</h1>
            </div>
            
            <div data-role="main" class="ui-content">

                <h4 class="connected">Last Update: <span id="now"></span></h4>
                
                <h3 class="status disconnected">Connecting...</h3>

                <a href="#heatOverridePopup" data-rel="popup" class="ui-btn heat" id="heatOverride">Heat to: <span class="heatSetPoint">68&degF</span> <span id="heatStatus" style="color:#FF4444"> ... ON!</span></a>
                <a href="#coolOverridePopup" data-rel="popup" class="ui-btn cool" id="coolOverride">Cool to: <span class="coolSetPoint">68&degF</span> <span id="coolStatus" style="color:#4444FF"> ... ON!</span></a>

                <div data-role="popup" id="heatOverridePopup" class="ui-content">
                    <h3><span class="heatSetPoint">68&degF</span></h3>
                    <div data-role="controlgroup" data-type="horizontal">
                        <label for="heatOverrideEnable">Override</label>
                        <input type="checkbox" id="heatOverrideEnable" name="heatOverrideEnable"/>
                        <input type="button" id="heatOverrideMinus" value="-" />
                        <input type="button" id="heatOverridePlus"  value="+" />
                    </div>
                </div>
                
                <div data-role="popup" id="coolOverridePopup" class="ui-content">
                    <h3><span class="coolSetPoint">68&degF</span></h3>
                    <div data-role="controlgroup" data-type="horizontal">
                        <label for="coolOverrideEnable">Override</label>
                        <input type="checkbox" id="coolOverrideEnable" name="coolOverrideEnable"/>
                        <input type="button" id="coolOverrideMinus" value="-" />
                        <input type="button" id="coolOverridePlus"  value="+" />
                    </div>
                </div>

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

        <div data-role="page" id="ConfigurePage" data-theme="b">
            
            <div data-role="header">
                <a href="#ContentsPage" class="ui-btn ui-icon-check ui-btn-icon-left ui-btn-icon-notext">Home</a>
                <h1>Configuration</h1>
            </div>
            
            <div data-role="main" class="ui-content">
        
                <div data-role="collapsible" data-collapsed="true">
                    <h1>General</h1>
                    <label for="doHeat">Enable Heat:</label>
                    <input type="checkbox" data-role="flipswitch" name="doHeat" id="doHeat" value="doHeat">
                    <label for="doCool">Enable A/C:</label>
                    <input type="checkbox" data-role="flipswitch" name="doCool" id="doCool" value="doCool">
                </div>

                <div data-role="collapsible">
                    <h1>Temperatures</h1>
                    <ul data-role="listview" data-inset="true" class="heat">
                        <li data-role="list-divider">Heater</li>
                        <li>
                            <label for="tempComfortable">Comfortable Heat Temperature:</label>
                            <input type="range" name="tempComfortable" id="tempComfortable" value="72" min="60" max="80">
                        </li>
                        <li>
                            <label for="tempSleeping">Sleeping Heat Temperature:</label>
                            <input type="range" name="tempSleeping" id="tempSleeping" value="72" min="60" max="80">
                        </li>
                        <li>
                            <label for="tempAway">Away Heat Temperature:</label>
                            <input type="range" name="tempAway" id="tempAway" value="72" min="60" max="80">
                        </li>
                    </ul>
                    <ul data-role="listview" data-inset="true" class="cool">
                        <li data-role="list-divider">Air Conditioner</li>
                        <li>
                            <label for="tempComfortable">Comfortable Cool Temperature:</label>
                            <input type="range" name="tempComfortable" id="tempComfortable" value="72" min="60" max="80">
                        </li>
                        <li>
                            <label for="tempSleeping">Sleeping Cool Temperature:</label>
                            <input type="range" name="tempSleeping" id="tempSleeping" value="72" min="60" max="80">
                        </li>
                        <li>
                            <label for="tempAway">Away Cool Temperature:</label>
                            <input type="range" name="tempAway" id="tempAway" value="72" min="60" max="80">
                        </li>
                    </ul>
                </div>

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Email Alerts</h1>
                    <label for="switch">Enable Email Alerts:</label>
                    <input type="checkbox" data-role="flipswitch" name="switch" id="switch">
                    <label for="smtp" class="ui-hidden-accessible">SMTP Address:</label>
                    <input type="text" name="smtp" id="smtp" placeholder="SMTP ex: smtp.gmail.com" data-clear-btn="true">
                    <label for="email" class="ui-hidden-accessible">Email Address:</label>
                    <input type="text" name="email" id="email" placeholder="Email Address" data-clear-btn="true">
                    <label for="email_pswd" class="ui-hidden-accessible">Password:</label>
                    <input type="password" name="email_passw" id="email_pswd" placeholder="Password" data-clear-btn="true">
                    <a href="#" class="ui-btn ui-btn-inline">Test Email</a>
                    <label for="email_restart">On Restart</label>
                    <input type="checkbox" name="email_restart" id="email_restart" value="email_restart">
                    <label for="email_oor">On Out of Range</label>
                    <input type="checkbox" name="email_oor" id="email_oor" value="email_oor">
                </div>

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Advanced</h1>
                    <h1>JUST WHO DO YOU THINK YOU ARE?</h1>
                </div>        
            </div>
            
            <div data-role="footer"><h1></h1></div>
            
        </div>

    </body>
</html>
