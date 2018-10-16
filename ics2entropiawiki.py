#!/usr/bin/env python3

import configparser
import re

from argparse import ArgumentParser
from datetime import timedelta, datetime
from ics import Calendar
from mwclient import Site
from dateutil.tz import tzlocal

import requests


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


class EntropiaEvent(object):
    """
    Parses an ics Event and converts it to an entropia-wiki suitable form
    """
    def __init__(self, event):
        """
        :param event: The event to be evaluated
        :type event: ics.event.Event
        """
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
        :rtype: str
        """
        if self.endtime - self.begintime > timedelta(days=1):
            return " - " + self.endtime.strftime("%a., %d.%m.%Y")
        else:
            return ""

    @property
    def is_past_event(self):
        """
        :return: Chech if the event lies in the past
        :rtype: bool
        """
        return self.endtime - datetime.now(tz=tzlocal()) < timedelta(days=1)

    @property
    def start_time(self):
        """
        :return: The starting time of the event
        :rtype: str
        """
        if not self.event.all_day:
            return self.begintime.strftime("%H:%M")
        else:
            return " "

    @property
    def description(self):
        """
        :return: The event's description
        :rtype: str
        """
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
        """
        :return: A wiki line describing the event
        :rtype: str
        """
        event_str = ("| " +
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


def append_past_events(past_events, wiki_user, wiki_pw, wiki_archive):
    """
    Append the "new" past events to the wiki archive page
    :param past_events: the past events that were not added to the events page
    :type past_events: list
    :param wiki_user: bot user for the wiki
    :type wiki_user: str
    :param wiki_pw: password for the wiki user
    :type wiki_pw: str
    :param wiki_archive: archive page
    :type wiki_archive: str
    :return: None
    :rtype: None
    """

    site = Site('entropia.de', path='/')
    site.login(wiki_user, wiki_pw)
    page = site.pages[wiki_archive]
    text = page.text().split('\n')
    last_table_position = 0

    for event in past_events:
        year_header = "== {} ==".format(event.endtime.strftime('%Y'))

        for index, txtline in enumerate(text):
            if txtline == '|}':
                last_table_position = index

        if str(event) not in text:
            continue

        if year_header in text:
            append_list = (
                '\n' +
                line_separator +
                str(event)
            )
            text = text[:last_table_position]+[append_list, ]+text[last_table_position:]
        else:
            append_list = (
                3*'\n' +
                year_header +
                archive_table_header +
                '\n' +
                line_separator +
                '\n' +
                str(event) +
                '\n|}'
            )
            text = text[:last_table_position+1]+[append_list, ]+text[last_table_position+1:]

    page.save("\n".join(text))

    return None


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

    event_strings = []
    past_event_strings = []
    past_events = []

    if file:
        calendar = Calendar(open(file))
    else:
        calendar = Calendar(requests.get(ics_url).text)

    for event in sorted(calendar.events, key=lambda ev: ev.begin):
        event = EntropiaEvent(event)
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
            past_events.append(event)
    append_past_events(past_events, wiki_user, wiki_pw, wiki_archive)
    termine = table_header+"\n"+"".join(event_strings)+"\n"+"".join(table_footer)
    print(termine)
    site = Site('entropia.de', path='/')
    site.login(wiki_user, wiki_pw)
    page = site.pages[wiki_page]
    if termine:
        page.save(termine, "Terminbot was here")


if __name__ == '__main__':
    main()