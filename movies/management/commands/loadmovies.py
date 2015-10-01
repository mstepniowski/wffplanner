import codecs
from datetime import datetime
from lxml import html

from django.core.management.base import BaseCommand

from movies.models import Movie, Screening


SITE_ROOT = 'http://www.wff.pl/filmy/'


class Command(BaseCommand):
    def handle(self, *file_names, **options):
        movies = {}
        for file_name in file_names:
            print file_name
            f = codecs.open(file_name, 'r', encoding='utf-8')
            e = html.fragment_fromstring(f.read())
            url = e.cssselect('.fastGrid a.button')[0].get('href')
            movie, _ = Movie.objects.get_or_create(url=url)
            movie.title = e.cssselect('h1')[0].text
            movie.info = self.load_extra_info(e)
            movie.save()
            movies[movie.title] = movie
            self.load_screenings(movie, e)

        self.postprocess(movies)

    def load_extra_info(self, e):
        ps = e.cssselect('p')
        if len(ps) > 2:
            return {'description': ps[2].text}
        else:
            return {}

    def load_screenings(self, movie, e):
        elements = e.cssselect('.title strong')
        for element in elements:
            parts = [s.strip() for s in element.text.split('>')]
            room = parts[0]
            dt = datetime.strptime(parts[2] + ' ' + parts[3], '%d.%m.%Y %H:%M')
            Screening.objects.get_or_create(movie=movie, date=dt, room=room)

    def postprocess(self, movies):
        pass
