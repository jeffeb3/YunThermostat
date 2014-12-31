//! collection of scripts to dynamically update things on a web page for the
//! arduino thermostat project.
//! @note This file is a SimpleTemplate file (http://bottlepy.org/docs/dev/stpl.html)
//! It is meant to be used with bottle, and won't load on it's own.

// *************** don't do this stuff until the page completely loads
$(document).ready(function()
{
    // Propogate the settings from the settings page.
    updateSettings();
    
    function updateSettings()
    {
        $.get("settings", function(data)
        {
            settings = JSON.parse(data);
            $("#doHeat").prop("checked",settings.doHeat);
            $("#doCool").prop("checked",settings.doCool);
            
            $("#heatTempComfortable").val(settings.heatTempComfortable);
            $("#heatTempSleeping").val(settings.heatTempSleeping);
            $("#heatTempAway").val(settings.heatTempAway);
            
            $("#coolTempComfortable").val(settings.coolTempComfortable);
            $("#coolTempSleeping").val(settings.coolTempSleeping);
            $("#coolTempAway").val(settings.coolTempAway);

            $("#doEmail").prop("checked", settings.doEmail);
            $("#smtp").val(settings.smtp);
            $("#email_from").val(settings.email_from);
            $("#email_to").val(settings.email_to);
            $("#email_passw").val('null'); // a sentinal value.
            $("#email_restart").prop("checked", settings.email_restart);
            $("#email_oor").prop("checked", settings.email_oor);
            
            // update which GUI elements are enabled.
            updateEnabled();
        });
    }

    // reset the settings when the 'X' is clicked.    
    $("#ConfigurePageResetButton").on('click', updateSettings);

    // change the form the the cool or heat are selected.
    $("#doHeat, #doCool, #doEmail").change(updateEnabled);

    function updateEnabled()
    {
        // hide/show all the heat controls.
        if ($("#doHeat").is(":checked"))
        {
            $(".heat").show();
        }
        else
        {
            $(".heat").hide();
        }
        
        // hide/show all the cool controls.
        if ($("#doCool").is(":checked"))
        {
            $(".cool").show();
        }
        else
        {
            $(".cool").hide();
        }        

        // hide/show all the email controls.
        if ($("#doEmail").is(":checked"))
        {
            $(".email-settings").show();
        }
        else
        {
            $(".email-settings").hide();
        }
    }
    
    // Test the email settings
    $("#email_test").on('mouseup', function()
    {
        $("#email_response").show();
        $("#email_response").text('Testing...');
        $.post('/emailTest',
        {
            "email_from" : $("#email_from").val(),
            "email_to" : $("#email_to").val(),
            "email_pswd" : $("#email_pswd").val(),
            "smtp" : $("#smtp").val(),
        },
        function(data)
        {
            $("#email_response").text(data);
        });
    });
});
