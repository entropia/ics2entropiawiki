# ics2entropiawiki

This project was started to automate the Calendar-Entries in the entropia-Wiki

It reads the Time and Dates of event from an ics file, this can be fetched from an URL

## Dependencies
```
ics
mwclient
```

## Usage
```
usage: ics2entropiawiki.py [-h] [-c CONFIG] [-u URL] [-f FILE]

optional arguments:
  -h, --help            show this help message and exit
  -c CONFIG, --config CONFIG
                        Configuration file path
  -u URL, --url URL     The URL under which the ICS-file can be retrieved
  -f FILE, --file FILE  Local ics file
```

### Configuration sample
```ini
[default]
url=https://example.com/sample.ics
wikiuser=WIKIBOT
wikipass=WIKIPASSWORD
wikipage=WIKIPAGE
```