#!/bin/python

import sys
import dateutil.parser
import ConfigParser
import os
import gflags
import httplib2

from datetime import timedelta, date
from monthdelta import monthdelta
from apiclient.discovery import build
from oauth2client.file import Storage
from oauth2client.client import OAuth2WebServerFlow
from oauth2client.tools import run

FLAGS = gflags.FLAGS

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.apontamento.cfg'))
identifier = config.get('Default', 'identifier')
client_id = config.get('Default', 'client_id')
client_secret = config.get('Default', 'client_secret')
user_agent = config.get('Default', 'user_agent')
developer_key = config.get('Default', 'developer_key')
calendar_id = config.get('Default', 'calendar_id')

# Set up a Flow object to be used if we need to authenticate. This
# sample uses OAuth 2.0, and we set up the OAuth2WebServerFlow with
# the information it needs to authenticate. Note that it is called
# the Web Server Flow, but it can also handle the flow for native
# applications
# The client_id and client_secret can be found in Google Developers Console
FLOW = OAuth2WebServerFlow(
    client_id=client_id,
    client_secret=client_secret,
    scope='https://www.googleapis.com/auth/calendar.readonly',
    user_agent=user_agent)

# To disable the local server feature, uncomment the following line:
# FLAGS.auth_local_webserver = False

# If the Credentials don't exist or are invalid, run through the native client
# flow. The Storage object will ensure that if successful the good
# Credentials will get written back to a file.
storage = Storage(os.path.expanduser('~/.apontamento.dat'))
credentials = storage.get()
if credentials is None or credentials.invalid == True:
  credentials = run(FLOW, storage)

# Create an httplib2.Http object to handle our HTTP requests and authorize it
# with our good Credentials.
http = httplib2.Http()
http = credentials.authorize(http)

# Build a service object for interacting with the API. Visit
# the Google Developers Console
# to get a developerKey for your own application.
service = build(serviceName='calendar', version='v3', http=http,
       developerKey=developer_key)



def FullTextQuery(service, text_query, months_ago=0):
    date_start = date.today() - monthdelta(months_ago)
    date_end = date_start + monthdelta(1)
    start_min = '%04d-%02d-01T00:00:00-03:00' % (date_start.year, date_start.month)
    start_max = '%04d-%02d-01T00:00:00-03:00' % (date_end.year, date_end.month)
    print "Periodo: %02d/%04d" % (date_start.month, date_start.year)
    max_results = 200
    return service.events().list(q=text_query, calendarId=calendar_id, timeMin=start_min, timeMax=start_max, maxResults=max_results).execute()


def getHours(delta):
    td = abs(delta)
    signal = ' '
    if (delta < td):
        signal = '-'
    hours = (td.days * 24) + (td.seconds // 3600)
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    return [signal, hours, minutes, seconds]

days = {}
weekends = {}
total = timedelta()
comments = {}

param = 0
if (len(sys.argv) > 1):
    param = int(sys.argv[1])
feed = FullTextQuery(service, identifier, param)

for an_event in feed['items']:
    if (an_event['summary'] != identifier):
        continue

    start = dateutil.parser.parse(an_event['start']['dateTime'])
    end = dateutil.parser.parse(an_event['end']['dateTime'])
    #print '\t\tStart time: %s - End time:   %s' % (start, end)

    duration = end - start
    total += duration
    if (start.day not in days):
        days[start.day] = timedelta()
        comments[start.day] = ''
    days[start.day] += duration
    comments[start.day] += an_event['description'] + ' ' if 'description' in an_event else ''
    if (start.weekday() in [5, 6]):
        weekends[start.day] = 1

hday = timedelta(hours=8)
for day in sorted(days.keys()):
    if (day in weekends.keys()):
        duration = days[day]
    elif (hday <= days[day]):
        duration = days[day] - hday
    else:
        duration = "-%s" % (hday - days[day])
    print "Dia %02d: %8s (%8s) %s" % (day, days[day], duration, comments[day])

print ''

expected = timedelta(hours=(len(days) - len(weekends)) * 8)
difference = total - expected
signal, hours, minutes, seconds = getHours(total)
print 'Total: %02d:%02d:%02d - %0.2f horas' % (hours, minutes, seconds, hours + (minutes / 60.0))
signal, hours, minutes, seconds = getHours(expected)
print 'Esperado: %02d horas' % (hours)
signal, hours, minutes, seconds = getHours(difference)
print 'Diferenca: %s%02d:%02d:%02d' % (signal, hours, minutes, seconds)
