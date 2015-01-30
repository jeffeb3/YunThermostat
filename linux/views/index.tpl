<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01 Transitional//EN" "http://www.w3.org/TR/html4/loose.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html; charset=utf-8">
        <title>Smart Temperature Sensor</title>
        <meta name="description" content="">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!--External source-->
        <link rel="stylesheet" href="javascript/jquery-mobile/jquery.mobile.css">
        <link href="static/launcher-icon-4x.png" rel="icon" type="image/x-icon" />
        <link rel="manifest" href="static/android_manifest.json"/>
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
                <h4>Uptime: <span id="uptime_number">?</span></h4>
                
                <h3 class="status disconnected">Connecting...</h3>

                <div data-role="collapsible" class="heat" data-collapsed="true">
                    <h1>Heat to: <span class="heatSetPoint">?</span>&degF <span id="heatStatus" style="color:#FF4444"> ... ON!</span></h1>

                    <fieldset data-role="controlgroup" data-type="horizontal">
                        <input type="button" id="heatOverrideMinus" value="-"/>
                        <input type="button" id="heatOverridePlus"  value="+"/>
                    </fieldset>
                    <fieldset data-role="controlgroup">
                        <label for="heatOverrideTemporary">Temporary Override</label>
                        <input type="radio" name="heatOverrideType" id="heatOverrideTemporary" value="temp" />
                        <label for="heatOverridePermanent">Vacation Override</label>
                        <input type="radio" name="heatOverrideType" id="heatOverridePermanent" value="perm" />
                    </fieldset>
                    <input type="button" id="heatClearOverride" value="Clear" />
                </div>
                
                <div data-role="collapsible" class="cool" data-collapsed="true">
                    <h1>Cool to: <span class="coolSetPoint">?</span>&degF <span id="coolStatus" style="color:#FF4444"> ... ON!</span></h1>

                    <fieldset data-role="controlgroup" data-type="horizontal">
                        <input type="button" id="coolOverrideMinus" value="-"/>
                        <input type="button" id="coolOverridePlus"  value="+"/>
                    </fieldset>
                    <fieldset data-role="controlgroup">
                        <label for="coolOverrideTemporary">Temporary Override</label>
                        <input type="radio" name="coolOverrideType" id="coolOverrideTemporary" value="temp" />
                        <label for="coolOverridePermanent">Vacation Override</label>
                        <input type="radio" name="coolOverrideType" id="coolOverridePermanent" value="perm" />
                    </fieldset>
                    <input type="button" id="coolClearOverride" value="Clear" />
                </div>
                
                <a href="#" data-role="button" data-inline="true" id="plotTimeAll">All</a>
                <a href="#" data-role="button" data-inline="true" id="plotTimeDay">Day</a>
                <a href="#" data-role="button" data-inline="true" id="plotTimeHour">Hour</a>
                <a href="#" data-role="button" data-inline="true" id="plotTimeMinutes">Minutes</a>

                <div data-role="collapsible" data-collapsed="false">
                    <h1>In: <span id="temperature">?</span> &degF Out: <span id="outsideTemperature">?</span>&degF</h1>
                    <div id="tempPlaceholder" class="plot-placeholder ui-body-inherit"></div>
                    <div id="tempLegend"      class="legend-placeholder ui-body-inherit"></div>
                </div>

                <div data-role="collapsible" data-collapsed="false">
                    <h1>Set Point</h1>
                    <div id="logicPlaceholder" class="plot-placeholder ui-body-inherit"></div>
                    <div id="logicLegend"      class="legend-placeholder ui-body-inherit"></div>
                </div>

                <div data-role="collapsible" data-collapsed="true">
                    <h1>System Health</h1>
                    <div id="healthPlaceholder" class="plot-placeholder"></div>
                    <div id="healthLegend"      class="legend-placeholder ui-body-inherit"></div>
                </div>

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Log</h1>
                    <table data-role="table" data-mode="columntoggle" class="ui-responsive table-stroke" id="logTable">
                        <thead>
                            <tr>
                                <th data-priority="3">Level</th>
                                <th data-priority="1">Message</th>
                                <th data-priority="2">Time</th>
                                <th data-priority="5">Log Name</th>
                                <th data-priority="5">Source</th>
                            </tr>
                        </thead>
                        <tbody id="appendLogs">
                            <tr>
                                <th class="logLevelINFO">INFO</th>
                                <td class="logMessage">Browser Started</td>
                                <td class="logTime"></td>
                                <td class="logName"></td>
                                <td class="logFile"></td>
                            </tr>
                        </tbody>
                    </table>
                </div>

            </div>
            
            <div data-role="footer"><h1></h1></div>
            
        </div>

        <form data-role="page" id="ConfigurePage" data-theme="b" action="/settings" method="post">
            
            <div data-role="header">
                <a href="#ContentsPage" onclick="$('#ConfigurePage').submit()" class="ui-btn ui-icon-check ui-btn-icon-left ui-btn-icon-notext">Save</a>
                <h1>Configuration</h1>
                <a href="#ContentsPage" id="ConfigurePageResetButton" class="ui-btn ui-icon-delete ui-btn-icon-right ui-btn-icon-notext">Reset</a>
            </div>
            
            <div data-role="main" class="ui-content">
        
                <div data-role="collapsible" data-collapsed="true">
                    <h1>General</h1>
                    <label for="doHeat">Enable Heat:</label>
                    <input type="checkbox" data-role="flipswitch" name="doHeat" id="doHeat" value=1 checked="true">
                    <label for="doCool">Enable A/C:</label>
                    <input type="checkbox" data-role="flipswitch" name="doCool" id="doCool" value=1 checked="true">
                </div>

                <div data-role="collapsible">
                    <h1>Temperatures</h1>
                    <ul data-role="listview" data-inset="true">
                        <li data-role="list-divider">Temerature Presets</li>
                        <li>
                            <div data-role="rangeslider">
                                <label for="heatTempComfortable">Comfortable Temperature:</label>
                                <input type="range" name="heatTempComfortable" id="heatTempComfortable" value="{{settings['heatTempComfortable']}}" min="60" max="90">
                                <input type="range" name="coolTempComfortable" id="coolTempComfortable" value="{{settings['coolTempComfortable']}}" min="60" max="90">
                            </div>
                        </li>
                        <li>
                            <div data-role="rangeslider">
                                <label for="heatTempSleeping">Sleeping Temperature:</label>
                                <input type="range" name="heatTempSleeping" id="heatTempSleeping" value="{{settings['heatTempSleeping']}}" min="60" max="90">
                                <input type="range" name="coolTempSleeping" id="coolTempSleeping" value="{{settings['coolTempSleeping']}}" min="60" max="90">
                            </div>
                        </li>
                        <li>
                            <div data-role="rangeslider">
                                <label for="heatTempAway">Away Temperature:</label>
                                <input type="range" name="heatTempAway" id="heatTempAway" value="{{settings['heatTempAway']}}" min="60" max="90">
                                <input type="range" name="coolTempAway" id="coolTempAway" value="{{settings['coolTempAway']}}" min="60" max="90">
                            </div>
                        </li>
                    </ul>
               </div>

                <div data-role="collapsible">
                    <h1>Awake Times</h1>
                    <ul data-role="listview" id="sleepTimes" data-inset="true">
                        % for day in days:
                        <li data-role="list-divider">{{day}}:</li>
                        <li>
                            <table><tbody><tr>
                                <!-- OMG, this is driving me crazy! I'll just do it in python! -->
                                <!-- TODO, redo this, again, it is toooooo hard to use-->
                                <td><p class="morning-time">{{times[day + 'Morn']}}</p></td>
                                <td width="100%">
                                    <div data-role="rangeslider" data-mini="true" class="no-number">
                                        <input type="range" name="{{day}}Morn"  id="{{day}}Morn"  data-mini="true" value="{{settings[day + 'Morn' ]}}" min="0" max="1439" step="5">
                                        <input type="range" name="{{day}}Night" id="{{day}}Night" data-mini="true" value="{{settings[day + 'Night']}}" min="0" max="1439" step="5">
                                    </div>
                                </td>
                                <td><p class="night-time">{{times[day + 'Night']}}</p></td>
                            </tr></tbody></table>
                        </li>
                        % end
                    </ul>
               </div>

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Email Alerts</h1>
                    <label for="doEmail">Enable Email Alerts:</label>
                    <input type="checkbox" data-role="flipswitch" name="doEmail" value=1 id="doEmail"></input>
                    <div class="email-settings">
                        <label for="smtp" class="email-settings">SMTP Address:</label>
                        <input type="text" name="smtp" class="email-settings" id="smtp" placeholder="SMTP ex: smtp.gmail.com:587" data-clear-btn="true">
                        <label for="email_from" class="email-settings">From Email Address:</label>
                        <input type="text" name="email_from" class="email-settings" id="email_from" placeholder="Email Address" data-clear-btn="true">
                        <label for="email_to" class="email-settings">To Email Addresses (comma separated):</label>
                        <input type="text" name="email_to" class="email-settings" id="email_to" placeholder="Email Addresses (comma delimited)" data-clear-btn="true">
                        <label for="email_pswd" class="email-settings ui-hidden-accessible">Password:</label>
                        <input type="password" name="email_passw" class="email-settings" id="email_pswd" placeholder="Password" data-clear-btn="true">
                        <a href="#ConfigurePage" class="email-settings ui-btn ui-btn-inline" id="email_test">Test Email</a>
                        <h4 id="email_response">Testing...</h4>
                        <label for="email_restart" class="email-settings">On Restart</label>
                        <input type="checkbox" name="email_restart" class="email-settings" id="email_restart" value=1>
                        <label for="email_oor" class="email-settings">On Out of Range</label>
                        <input type="checkbox" name="email_oor" class="email-settings" id="email_oor" value=1></input>
                    </div>
                </div>

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Weather</h1>
                    <label for="weather_state">State</label>
                    <input type="text" name="weather_state" id="weather_state" placeholder="CO" data-clear-btn="true"></input>
                    <label for="weather_city">City</label>
                    <input type="text" name="weather_city" id="weather_city" placeholder="Denver" data-clear-btn="true"></input>
                    <label for="weather_api_key">API key for <a href="http://www.wunderground.com/weather/api/d/pricing.html" class="ui-btn ui-btn-inline">Wunderground.com </a></label>
                    <input type="text" name="weather_api_key" id="weather_api_key" data-clear-btn="true"></input>
                    
                </div>        

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Thing Speak</h1>
                    <label for="doThingspeak">Enable ThingSpeak:</label>
                    <input type="checkbox" data-role="flipswitch" name="doThingspeak" value=1 id="doThingspeak"></input>
                    <label for="thingspeak_api_key">API key for <a href="http://thinkspeak.com" class="ui-btn ui-btn-inline">thingspeak.com </a> channel.</label>
                    <input type="text" name="thingspeak_api_key" id="thingspeak_api_key" data-clear-btn="true"></input>
                    <label for="thingspeak_location_api_key">API key for <a href="http://thinkspeak.com" class="ui-btn ui-btn-inline">thingspeak.com </a> channel for location awareness.</label>
                    <input type="text" name="thingspeak_location_api_key" id="thingspeak_location_api_key" data-clear-btn="true"></input>
                    <label for="thingspeak_location_channel">Channel for <a href="http://thinkspeak.com" class="ui-btn ui-btn-inline">thingspeak.com </a> location awareness.</label>
                    <input type="text" name="thingspeak_location_channel" id="thingspeak_location_channel" data-clear-btn="true"></input>
                </div>        

                <div data-role="collapsible" data-collapsed="true">
                    <h1>Advanced</h1>
                    <h1>JUST WHO DO YOU THINK YOU ARE?</h1>
                </div>        
            </div>
            
            <div data-role="footer"><h1></h1></div>

        </form>
    </body>
</html>
