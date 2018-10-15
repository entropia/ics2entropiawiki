#!/usr/bin/env python3

import configparser
import requests
import re

from ics import Calendar
from argparse import ArgumentParser
from datetime import timedelta, datetime
from mwclient import Site
from dateutil.tz import tzlocal

table_header = """
{| class="termine" border="1" cellspacing="0" cellpadding="5" width="100%" style="border-collapse:collapse;" 
! style="width:250px;" |  Datum              !! style="width:50px;" | Zeit  !! Ort                  !! Beschreibung\
"""

archive_table_header = """
{| class="termine" border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse;" width="100%"
|width=15%|'''Datum'''
|width=6%|'''Zeit'''
|width=15%|'''Ort'''
|width=69%|'''Beschreibung'''
"""

table_footer = ("|}",
                "\n",
                "Weitere Links: [[Vorlage:Termine|Termine]] ",
                "([https://entropia.de/index.php?title=Vorlage:Termine&action=edit Bearbeiten]),",
                " [[Vorlage:Vergangene_Termine|Vergangene Termine]], [[Anfahrt]]"
                )
line_separator = "|-"


class Event(object):
    def __init__(self, event):
        self.event = event
        self.begintime = event.begin.datetime.astimezone()
        self.endtime = event._end_time.datetime.astimezone()

    @property
    def location(self):
        locations = {
            "entropia": "[[Anfahrt|Entropia]]",
        }

        location = " "

        if self.event.location:
            location = self.event.location
            if location.lower() in locations.keys():
                location = locations[location.lower()]

        return location

    @property
    def begin_date(self):
        """
        :return: Entropia-Wiki formated begin time
        :rtype: str
        """
        return self.begintime.strftime("%a., %d.%m.%Y")

    @property
    def end_date(self):
        """
        :return: Entropia-Wiki formated end time
        """
        if self.endtime - self.begintime > timedelta(days=1):
            return " - " + self.endtime.strftime("%a., %d.%m.%Y")
        else:
            return ""

    @property
    def is_past_event(self):
        return self.endtime - datetime.now(tz=tzlocal()) < timedelta(days=1)

    @property
    def start_time(self):
        if not self.event.all_day:
            return self.begintime.strftime("%H:%M")
        else:
            return " "

    @property
    def description(self):
        links = None
        event = self.event

        if self.event.description:
            links = re.findall("^Link:(.*)$", event.description)

        if links and event.name:
            description = "["+links[0]+" "+event.name+"]"
        elif not self.event.name:
            description = "N.A."
        else:
            description = event.name

        return description

    def __str__(self):
        event_str =("| "+
                    self.begin_date +
                    self.end_date +
                    " || " +
                    self.start_time +
                    " || " +
                    self.location +
                    " || " +
                    self.description
                    )

        return event_str


def main():
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config",
        default="/etc/baikal2wiki/config.ini",
        dest="configfile",
        help="Configuration file path",
        metavar="CONFIG"
    )
    parser.add_argument(
        "-u", "--url",
        dest="ics_url",
        help="The URL under which the ICS-file can be retrieved",
        metavar="URL",
    )
    parser.add_argument(
        "-f", "--file",
        dest="local_file",
        help="Local ics file",
        metavar="FILE"
    )
    parser.add_argument(
        "--wiki-user",
        dest="wiki_user",
        help="Wiki user",
        metavar="WIKIUSER"
    )
    parser.add_argument(
        "--wiki-password",
        dest="wiki_pw",
        help="Wiki user's password",
        metavar="WIKIPW"
    )
    parser.add_argument(
        "--wiki-page",
        dest="wiki_page",
        help='Wiki page',
        metavar='WIKIPAGE'
    )
    parser.add_argument(
        "--wiki-archive",
        dest="wiki_archive",
        help='Wiki archive',
        metavar='WIKIARCHIVE'
    )

    args = parser.parse_args()
    configfile = args.configfile
    ics_url = args.ics_url
    file = args.local_file
    wiki_user = args.wiki_user
    wiki_pw = args.wiki_pw
    wiki_page = args.wiki_page
    wiki_archive = args.wiki_archive

    if configfile:
        config = configparser.ConfigParser()
        config.read(configfile)
        try:
            ics_url = config["default"]["url"]
            wiki_user = config["wiki"]["user"]
            wiki_pw = config["wiki"]["pass"]
            wiki_page = config["wiki"]["page"]
            wiki_archive = config["wiki"]["archive"]
            print(ics_url)
        except KeyError as e:
            print("Please have a look at the sample config provided with the package")
            raise e

    table_header = """
    {| class="termine" border="1" cellspacing="0" cellpadding="5" width="100%" style="border-collapse:collapse;" 
    ! style="width:250px;" |  Datum              !! style="width:50px;" | Zeit  !! Ort                  !! Beschreibung\
    """
    table_footer = ("|}",
                    "\n",
                    "Weitere Links: [[Vorlage:Termine|Termine]] ",
                    "([https://entropia.de/index.php?title=Vorlage:Termine&action=edit Bearbeiten]),",
                    " [[Vorlage:Vergangene_Termine|Vergangene Termine]], [[Anfahrt]]"
                    )
    line_separator = "|-\n| "

    event_strings = []
    past_event_strings = []

    if file:
        calendar = Calendar(open(file))
    else:
        calendar = Calendar(requests.get(ics_url).text)

    for event in sorted(calendar.events, key=lambda ev: ev.begin):
        event = Event(event)
        if not event.is_past_event:
            event_strings.append(
                "\n" +
                line_separator +
                str(event)
            )
        else:
            past_event_strings.append(
                "\n" +
                line_separator +
                str(event)
            )

    termine = table_header+"\n"+"".join(event_strings)+"\n"+"".join(table_footer)
    vergangene_termine = table_header+"\n"+"".join(past_event_strings)+"\n"+"".join(table_footer)
    print(termine)
    print(vergangene_termine)
    site = Site('entropia.de', path='/')
    site.login(wiki_user, wiki_pw)
    page = site.pages[wiki_page]
    if termine:
        page.save(termine, "Terminbox was here")


if __name__ == '__main__':
    main()