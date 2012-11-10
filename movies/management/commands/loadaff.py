import os
import re
from datetime import datetime
from lxml import html

from django.core.management.base import BaseCommand

from movies.models import Movie, Screening, Festival


URL_TEMPLATE = 'http://www.americanfilmfestival.pl/film.do?id=%s'


class Command(BaseCommand):
    def handle(self, *file_names, **options):
        aff = Festival.objects.get(name='American Film Festival')
        
        for file_name in file_names:
            print file_name
            document = html.parse(file_name)
            base, ext = os.path.splitext(os.path.basename(file_name))
            movie, _ = Movie.objects.get_or_create(url=URL_TEMPLATE % base)
            movie.festival = aff
            movie.title = document.getroot().cssselect('.tytulfilmu div')[0].text
            movie.save()
            self.load_screenings(movie, document.getroot())

    def load_screenings(self, movie, root):
        for row in root.cssselect('.seanse td'):
            t = row.cssselect('.termin')
            if len(t) == 0:
                continue
                
            match = re.match(r'(\d+) listopada, (\d\d):(\d\d)', t[0].text.strip())
            if not match:
                continue
                
            day = int(match.group(1))
            hour = int(match.group(2))
            minute = int(match.group(3))
            room = row.cssselect('.sala')[0].text.strip()
            
            Screening.objects.get_or_create(
                movie=movie,
                date=datetime(2012, 11, day, hour, minute),
                room=room)
