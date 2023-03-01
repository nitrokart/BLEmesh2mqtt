#!/bin/bash

#Starting BLEmesh2mqtt

pwd
cd /
ls

cd /config
pwd
ls -la

cd /opt/hass-ble-mesh/
ls -la


service dbus start
/usr/libexec/bluetooth/bluetooth-meshd

python3 gateway.py --basedir /config --reload

/usr/libexec/bluetooth/bluetooth-meshd &

python3 gateway.py --basedir /config --reload &
/bin/bash