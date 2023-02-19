#!/bin/bash

#Starting BLEmesh2mqtt

who

service dbus start

/usr/libexec/bluetooth/bluetooth-meshd

python3 gateway.py --basedir /config --reload

/usr/libexec/bluetooth/bluetooth-meshd &

python3 gateway.py --basedir /config --reload &
/bin/bash