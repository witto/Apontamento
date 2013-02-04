#!/bin/python

import gdata.calendar.data
import gdata.calendar.client
import gdata.acl.data
import atom.data
import time
import sys
from datetime import timedelta, date
from monthdelta import monthdelta
import dateutil.parser
import ConfigParser
import os

def FullTextQuery(calendar_client, feed_uri, text_query='Tennis', months_ago=0):
  date_start = date.today() - monthdelta(months_ago)
  date_end = date_start + monthdelta(1)
  query = gdata.calendar.client.CalendarEventQuery(text_query=text_query)
  query.start_min = '%04d-%02d-01' % (date_start.year, date_start.month)
  query.start_max = '%04d-%02d-01' % (date_end.year, date_end.month)
  print "Periodo: %02d/%04d" % (date_start.month, date_start.year)
  query.max_results = 200
  return calendar_client.GetCalendarEventFeed(uri=feed_uri, q=query)

def getHours(delta):
    td = abs(delta)
    signal = ' '
    if (delta < td) :
        signal = '-'
    hours = (td.days * 24) + (td.seconds // 3600)
    minutes = (td.seconds % 3600) // 60
    seconds = td.seconds % 60
    return [signal, hours, minutes, seconds]

config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.apontamento.cfg'))

calendar_client = gdata.calendar.client.CalendarClient()
username = config.get('Default', 'username')
visibility = config.get('Default', 'visibility')
identifier = config.get('Default', 'identifier')
projection = 'full'
feed_uri = calendar_client.GetCalendarEventFeedUri(calendar=username, visibility=visibility, projection=projection)

days = {}
weekends = {}
total = timedelta()
comments = {}

param = 0
if (len(sys.argv) > 1):
  param = int(sys.argv[1])
feed = FullTextQuery(calendar_client, feed_uri, identifier, param)
for i, an_event in enumerate(feed.entry):
  if (an_event.title.text != identifier):
    continue
  #print '\t%s. %s' % (i, an_event.title.text,)
  for a_when in an_event.when:
      start = dateutil.parser.parse(a_when.start)
      end   = dateutil.parser.parse(a_when.end)
      #print '\t\tStart time: %s - End time:   %s' % (start,end)
      duration = end - start
      total += duration
      if (start.day not in days):
         days[start.day] = timedelta()
         comments[start.day] = ''
      days[start.day] += duration
      comments[start.day] += an_event.content.text + ' ' if an_event.content.text else ''
      if (start.weekday() in [5,6]):
         weekends[start.day] = 1

hday = timedelta(hours=8)
for day in sorted(days.keys()):
    if (hday <= days[day]):
        print "Dia %02d: %8s ( %s) %s" % (day, days[day], days[day] - hday, comments[day])
    else:
        print "Dia %02d: %8s (-%s) %s" % (day, days[day], hday - days[day], comments[day])

print ''

expected = timedelta(hours=(len(days) - len(weekends)) * 8)
difference = total - expected
signal, hours, minutes, seconds = getHours(total)
print 'Total: %02d:%02d:%02d - %0.2f horas' % (hours, minutes, seconds, hours + (minutes / 60.0))
signal, hours, minutes, seconds = getHours(expected)
print 'Esperado: %02d horas' % (hours)
signal, hours, minutes, seconds = getHours(difference)
print 'Diferenca: %s%02d:%02d:%02d' % (signal, hours, minutes, seconds)

