//! collection of scripts to dynamically update things on a web page for the
//! arduino thermostat project.
//! @note This file is a SimpleTemplate file (http://bottlepy.org/docs/dev/stpl.html)
//! It is meant to be used with bottle, and won't load on it's own.

// *************** don't do this stuff until the page completely loads
$(document).ready(function()
{
    $("#doHeat, #doCool").change(function()
    {
        var isChecked = $(this).is(":checked") ? 1 : 0;
        $.ajax({
            url: '/action',
            type: 'POST',
            data: {
                id: $(this).get(0).id,
                value: isChecked
            }
        });

        updateEnabled();
    });

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
    }
    
});
