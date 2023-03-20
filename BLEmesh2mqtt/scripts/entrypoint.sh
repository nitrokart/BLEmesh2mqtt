#!/bin/bash

# Starting BLEmesh2mqtt
cd /config
service dbus start
/usr/libexec/bluetooth/bluetooth-meshd &

cd /opt/hass-ble-mesh/
python3 gateway.py --basedir /config --reload
#/bin/bash