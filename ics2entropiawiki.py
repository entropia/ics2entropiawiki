#!/usr/bin/env python3

import configparser
import requests
import re

from ics import Calendar
from argparse import ArgumentParser
from datetime import timedelta, datetime
from mwclient import Site

def main():
    parser = ArgumentParser()
    parser.add_argument("-c", "--config",
                        default="/etc/baikal2wiki/config.ini",
                        dest="configfile",
                        help="Configuration file path",
                        metavar="CONFIG"
                        )
    parser.add_argument("-u","--url",
                        dest="ics_url",
                        help="The URL under which the ICS-file can be retrieved",
                        metavar="URL",
                        )
    parser.add_argument("-f","--file",
                        dest="local_file",
                        help="Local ics file",
                        metavar="FILE"
                        )

    args = parser.parse_args()
    configfile = args.configfile
    ics_url = args.ics_url
    file = args.local_file

    if not ics_url or file:
        config = configparser.ConfigParser()
        config.read(configfile)
        try:
            ics_url=config["default"]["url"]
            wiki_user=config["default"]["wikiuser"]
            wiki_pw=config["default"]["wikipass"]
            wiki_page=config["default"]["wikipage"]
            print(ics_url)
        except KeyError as e:
            print("Please have a look at the sample config provided with the package")
            raise e

    table_header = """
    {| class="termine" border="1" cellspacing="0" cellpadding="5" width="100%" style="border-collapse:collapse;" 
    ! style="width:250px;" |  Datum              !! style="width:50px;" | Zeit  !! Ort                  !! Beschreibung"""
    table_footer = ("|}",
                    "\n",
                    "Weitere Links: [[Vorlage:Termine|Termine]] ",
                    "([https://entropia.de/index.php?title=Vorlage:Termine&action=edit Bearbeiten]),",
                    " [[Vorlage:Vergangene_Termine|Vergangene Termine]], [[Anfahrt]]"
                    )
    line_separator = "|-\n| "
    locations = {
        "entropia":"[[Anfahrt|Entropia]]",
    }

    cal_strings=[]

    if file:
        calendar = Calendar(open(file))
    else:
        calendar = Calendar(requests.get(ics_url).text)

    for event in sorted(calendar.events, key=lambda ev: ev.begin):
        begintime = event.begin.datetime.astimezone()
        # here an internal variable is called since event.end is off by one
        # https://github.com/C4ptainCrunch/ics.py/issues/92
        endtime = event._end_time.datetime.astimezone()
        begin_day_fmt = begintime.strftime("%a., %d.%m.%Y")
        end_day_fmt = endtime.strftime("%a., %d.%m.%Y")

        start_time = ""
        end_data = ""
        location = ""
        links = None

        if endtime - datetime.now() > timedelta(days=1):
            continue

        if not event.all_day:
            start_time = begintime.strftime("%H:%M")

        if endtime - begintime > timedelta(days=1):
            end_date = " - "+end_day_fmt

        if event.location:
            location = event.location
            if event.location.lower() in locations.keys():
                location = locations[event.location.lower()]

        if event.description:
            links = re.findall("^Link:(.*)$",event.description)

        if links:
            description = "["+links[0]+" "+event.name+"]"
        elif not event.name:
            description = "N.A."
        else:
            description = event.name

        cal_strings.append("\n" + line_separator +
                           begin_day_fmt + end_date + " || " +
                           start_time +" || " +
                           location +" || " +
                           description
                           )

    termine = table_header+"\n"+"".join(cal_strings)+"\n"+"".join(table_footer)
    print(termine)
    site = Site('entropia.de',path='/')
    site.login(wiki_user,wiki_pw)
    page=site.pages[wiki_page]
    if termine:
        page.save(termine, "Terminbox was here")


if __name__ == '__main__':
    main()