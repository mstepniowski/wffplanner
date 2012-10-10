import datetime
import re
import vobject
from collections import defaultdict
from dateutil import tz

from django.db import models
from django.contrib.auth.models import User

from movies.fields import JSONField



class Movie(models.Model):
    url = models.CharField(max_length=250, primary_key=True)
    title = models.CharField(max_length=250, null=False, blank=False)
    info = JSONField(json_type=dict, default='{}', null=False, blank=False)
    collection = models.ForeignKey('self', null=True, blank=True)
    
    def __unicode__(self):
        return self.title


class Screening(models.Model):
    movie = models.ForeignKey(Movie)
    date = models.DateTimeField(null=False)
    room = models.CharField(max_length=250, null=False, blank=False)
    attendees_count = models.IntegerField(null=False, blank=False, default=0)
    
    def __unicode__(self):
        return u'%s: %s %s' % (self.movie.title, self.room, self.date)


class Checkin(models.Model):
    user = models.ForeignKey(User)
    screening = models.ForeignKey(Screening)
    facebook_id = models.CharField(max_length=30, db_index=True)
    
    class Meta:
        unique_together = ('user', 'screening')


class Calendar(object):
    def __init__(self, screenings=None):
        self.screenings = (screenings if screenings is not None
                           else Screening.objects.filter(movie__collection_id=None))

    def rooms(self):
        return set(screening.room for screening in self.screenings)

    def screenings_for_room(self, room):
        return [screening for screening in self.screenings if screening.room == room]

    def dates(self):
        return set(screening.date for screening in self.screenings)
    
    def dates_for_room(self, room):
        return set(screening.date for screening in self.screenings_for_room(room))

    def screenings_by_hour(self, room):
        result = defaultdict(list)
        for screening in self.screenings_for_room(room):
            result[(screening.date.hour, screening.date.minute)].append(screening)
        return result

    def days(self):
        return set(screening.date.day for screening in self.screenings)

    def rows(self):
        result = []
        position = 35
        for room in self.sort_rooms(self.rooms()):
            room_row = {'name': room, 'screenings': [], 'position': position}
            for (hour, minute), screenings in sorted(self.screenings_by_hour(room).items()):
                room_row['screenings'].append({'room': room,
                                           'time': '%02d:%02d' % (hour, minute),
                                           'screenings': self.screenings_by_day(screenings)})
            room_row['height'] = len(self.screenings_by_hour(room)) * 100
            position += room_row['height']
            result.append(room_row)
        return result

    def screenings_by_day(self, screenings):
        result = defaultdict(list)
        for screening in screenings:
            result[screening.date.day].append(screening)
        for day in sorted(self.days()):
            yield result[day]

    def sort_rooms(self, rooms):
        result = []
        # Multikino goes first
        result.extend(sorted(room for room in rooms if room.startswith('MULTIKINO')))
        # ...then the rest
        result.extend(sorted(room for room in rooms if not room.startswith('MULTIKINO')))
        return result
    

def generate_ical_feed(user):
    """Returns an iCal feed for passed in user."""
    return generate_ical([{'name': screening.movie.title,
                           'description': screening.movie.info['description'],
                           'room': screening.room,
                           'dtstart': screening.date,
                           'dtend': screening.date + datetime.timedelta(minutes=screening.movie.info['duration'])}
                          for screening in Screening.objects.filter(checkin__user=user)])


def generate_uid(event):
    name = re.sub(r'[^a-zA-Z0-9-.]', '-', event['name'].lower())
    room = re.sub(r'[^a-zA-Z0-9-.]', '-', event['room'].lower())
    return 'wff-2012-' + name + '-' + room + '-' + str(event['dtstart'].day) + '-' + str(event['dtstart'].hour)

                        
def generate_ical(events, get_uid=generate_uid):
    """Generates an iCalendar feed for a list of `events`. After
    saving the feed to a file, it can be imported directly to iCal,
    Outlook, Google Calendar and other calendaring programs. Users can
    also subscribe to such feed via URL. The file will then be
    downloaded regularly and the calendar will be automatically
    updated.

    Each event should be a dict with "name", "speaker", "description",
    "dtstart" and "dtend" keys. All dates should be in UTC timezone.
    Example::

        {'name': 'Good API design',
        'description': '...',
        'dtstart': datetime.datetime(2011, 6, 20, 9, 30),
        'dtend': datetime.datetime(2011, 6, 20, 10, 30)}

    A unique identificator for each event is generated using `get_uid`
    function (by default it's a slug of the title). The UID is used
    when the user subscribes to the calendar to identify the events
    that should be updated.
    """
    timezone = tz.gettz('Europe/Warsaw')
    calendar = vobject.iCalendar()
    for event in events:
        vevent = calendar.add('vevent')
        
        vevent.add('summary').value = event['name']
        vevent.add('description').value = event['description']
        vevent.add('dtstart').value = event['dtstart'].replace(tzinfo=timezone)
        vevent.add('dtend').value = event['dtend'].replace(tzinfo=timezone)
        vevent.add('dtstamp').value = datetime.datetime.now().replace(tzinfo=timezone)
        vevent.add('uid').value = get_uid(event)
        vevent.add('uri').value = 'http://wffplanner.stepniowski.com/'
        vevent.add('location').value = event['room']
    
    calendar.add('X-WR-CALNAME').value = 'Warsaw Film Festival'
    
    return calendar.serialize()
