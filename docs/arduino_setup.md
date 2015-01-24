
# Arduino Setup

1. Update the firmware.
    [http://arduino.cc/en/Tutorial/YunSysupgrade]

1. Configure it for your password/wifi settings.

1. Set the REST configuration to Open.

1. Upgrade the storage with an SD card:
    [http://arduino.cc/en/Tutorial/ExpandingYunDiskSpace]

1. upload the thermostat.ino sketch

## External Dependencies:

The Yun does not come with all the components we need to run the Thermostat.

First, install the python installer pip.

    opkg update                 # updates the available packages list
    opkg install distribute     # it contains the easy_install command line tool
    opkg install python-openssl # adds ssl support to python
    easy_install pip            # installs pip

Second, install the python dependencies:

    pip install bottle          # Used for serving the web page
    pip install paste           # Server backend needed to run parallel web components with bottle
    
Third, install the javascript libraries into the javascript folder.

todo...

1. [jquery 1.7.2]()
1. [jquery-mobile 1.4.5]()
1. [jquery-flot 0.8.3]()
    
## Install the thermostat files

    ssh root@arduino.local mkdir -p /usr/local/bin/thermostat
    scp -r linux/* root@arduino.local:/usr/local/bin/thermostat/

## Run the thermostat from startup:
add this line to the /etc/rc.local on your Arduino Yun:

    (sleep 30; /usr/local/bin/thermostat/thermostat.sh)&

This will run after the wifi has connected. It will wait 30 seconds (the sleep)
and then run the thermostat app in the background (see the '&').