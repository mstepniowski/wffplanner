from collections import defaultdict

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
    
