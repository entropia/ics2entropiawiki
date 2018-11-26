#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""ics2entropiawiki

Read an ics file with the entropia events and insert them in to the
entropia homepage wiki.

Example:

        $ ics2entropiawiki.py --config /etc/ics2entropiawiki/config.ini

Inserts events not in the past to the "Termine" Wiki page and appends past
events to the "Vergangene_Termine" Site
"""
import configparser
import re
import requests
import locale

from argparse import ArgumentParser
from datetime import timedelta, datetime
from ics import Calendar
from mwclient import Site
from dateutil.tz import tzlocal

TABLE_HEADER = """
{| class="termine" border="1" cellspacing="0" cellpadding="5" width="100%" style="border-collapse:collapse;" 
! style="width:250px;" |  Datum              !! style="width:50px;" | Zeit  !! Ort                  !! Beschreibung\
"""

ARCHIVE_TABLE_HEADER = """
{| class="termine" border="1" cellspacing="0" cellpadding="5" style="border-collapse:collapse;" width="100%"
|width=15%|'''Datum'''
|width=6%|'''Zeit'''
|width=15%|'''Ort'''
|width=69%|'''Beschreibung'''
"""

TABLE_FOOTER = (
    "|}",
    "\n",
    "Weitere Links: [[Vorlage:Termine|Termine]] ",
    "([https://entropia.de/index.php?title=Vorlage:Termine&action=edit Bearbeiten]),",
    " [[Vorlage:Vergangene_Termine|Vergangene Termine]], [[Anfahrt]]"
)

LINE_SEPARATOR = "|-\n"

try:
    locale.setlocale(locale.LC_ALL, 'de_DE.utf8')
except:
    pass

class EntropiaEvent():
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
        """
        Retrieve the location of an event
        :return: location
        :rtype: str
        """
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
        :return: Entropia-Wiki formatted begin time
        :rtype: str
        """
        return self.begintime.strftime("%a., %d.%m.%Y")

    @property
    def end_date(self):
        """
        :return: Entropia-Wiki formatted end time
        :rtype: str
        """
        end_date = ""

        if self.endtime - self.begintime > timedelta(days=1):
            end_date = " - " + self.endtime.strftime("%a., %d.%m.%Y")

        return end_date


    @property
    def is_past_event(self):
        """
        :return: Check if the event lies in the past
        :rtype: bool
        """
        return self.endtime - datetime.now(tz=tzlocal()) < timedelta(days=1)

    @property
    def start_time(self):
        """
        :return: The starting time of the event
        :rtype: str
        """
        start_time = " "

        if not self.event.all_day:
            start_time = self.begintime.strftime("%H:%M")

        return start_time

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
        return ("| " +
                self.begin_date +
                self.end_date +
                " || " +
                self.start_time +
                " || " +
                self.location +
                " || " +
                self.description
                )


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
                LINE_SEPARATOR +
                str(event)
            )
            text = text[:last_table_position]+[append_list, ]+text[last_table_position:]
        else:
            append_list = (
                3 * '\n' +
                year_header +
                ARCHIVE_TABLE_HEADER +
                '\n' +
                LINE_SEPARATOR +
                '\n' +
                str(event) +
                '\n|}'
            )
            text = text[:last_table_position+1]+[append_list, ]+text[last_table_position+1:]

    page.save("\n".join(text))


def get_args():
    """
    Retrieve arguments from the command line, the config file respectively
    :return: Parsed arguments from command line, config file
    :rtype: list
    """
    parser = ArgumentParser()
    parser.add_argument(
        "-c", "--config",
        default="/etc/ics2entropiawiki/config.ini",
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
    parser.add_argument(
        "-d", "--debug",
        dest="debug",
        action="store_true",
        default=False
    )

    args = parser.parse_args()
    configfile = args.configfile
    ics_url = args.ics_url
    file = args.local_file
    wiki = {
        'user': args.wiki_user,
        'pass': args.wiki_pw,
        'page': args.wiki_page,
        'archive': args.wiki_archive,
    }
    debug = args.debug

    if configfile:
        config = configparser.ConfigParser()
        config.read(configfile)
        try:
            ics_url = config["default"]["url"]
            wiki = config["wiki"]
        except KeyError as error:
            print("Please have a look at the sample config provided with the package")
            raise error

    return ics_url, file, wiki, debug


def deradicalise_ical( ics ):
    """
    :param ics: input file
    :type ics: str
    :return: file with remove radicale_headers
    """
    deradicalised = ""
    for line in ics.splitlines():
        if 'X-RADICALE-NAME:' not in line:
            deradicalised += "\n"+line

    return deradicalised


def main():
    """
    :return: None
    :rtype: None
    """
    ics_url, file, wiki,debug = get_args()
    event_strings = []
    past_event_strings = []
    past_events = []

    if file:
        calendar = Calendar(deradicalise_ical(open(file).read()))
    else:
        calendar = Calendar(deradicalise_ical(requests.get(ics_url).text))

    for event in sorted(calendar.events, key=lambda ev: ev.begin):
        event = EntropiaEvent(event)
        if not event.is_past_event:
            event_strings.append(
                "\n" +
                LINE_SEPARATOR +
                str(event)
            )
        else:
            past_event_strings.append(
                "\n" +
                LINE_SEPARATOR +
                str(event)
            )
            past_events.append(event)

    append_past_events(past_events, wiki['user'], wiki['pass'], wiki['archive'])
    termine = TABLE_HEADER + "\n" + "".join(event_strings) + "\n" + "".join(TABLE_FOOTER)
    if debug:
        print(termine)
    site = Site('entropia.de', path='/')
    site.login(wiki['user'], wiki['pass'])
    page = site.pages[wiki['page']]
    if termine:
        page.save(termine, "Terminbot was here")
        page.purge()


if __name__ == '__main__':
    main()
