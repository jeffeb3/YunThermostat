

To setup the arduino:

1) Update the firmware.
http://arduino.cc/en/Tutorial/YunSysupgrade

1) Configure it for your password/wifi settings.

1) Set the REST configuration to Open.

1) Upgrade the storage with an SD card:
http://arduino.cc/en/Tutorial/ExpandingYunDiskSpace

1) upload the thermostat.ino sketch

Python:
opkg update #updates the available packages list
opkg install distribute #it contains the easy_install command line tool
opkg install python-openssl #adds ssl support to python
easy_install pip #installs pip

pip install paste
pip install bottle

install:

ssh root@arduino.local mkdir -p /usr/local/bin/thermostat
scp -r linux/* root@arduino.local:/usr/local/bin/thermostat/

run at startup:
add this line to the /etc/rc.local:
(sleep 120; /usr/local/bin/thermostat/thermostat.sh)&
