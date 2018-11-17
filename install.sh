#!/bin/bash

ICS2EDIR=/opt/ics2entropiawiki
VENVDIR=/opt/ics2entropiawiki-venv
CONFDIR=/etc/ics2entropiawiki

mkdir $VENVDIR 
virtualenv -p /usr/bin/python3 $VENVDIR

cp ics2entropiawiki.py $ICS2EDIR
cp sample_config.ini $CONFDIR

$VENVDIR/bin/pip3 install -r requirements.txt
