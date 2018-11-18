#!/bin/bash

ICS2EDIR=/opt/ics2entropiawiki
VENVDIR=$ICS2EDIR/venv
CONFDIR=/etc/ics2entropiawiki

mkdir -p $VENVDIR 
virtualenv -p /usr/bin/python3 $VENVDIR

cp ics2entropiawiki.py $ICS2EDIR/

mkdir -p $CONFDIR
cp sample_config.ini $CONFDIR/config.ini

$VENVDIR/bin/pip3 install -r requirements.txt

cp systemd/* /etc/systemd/system/
systemctl daemon-reload
