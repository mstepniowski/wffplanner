from datetime import datetime
from lxml import html

from django.core.management.base import BaseCommand

from movies.models import Movie, Screening


SITE_ROOT = 'http://www.wff.pl/filmy/'


class Command(BaseCommand):
    def handle(self, *file_names, **options):
        Movie.objects.all().delete()
        Screening.objects.all().delete()
        
        for file_name in file_names:
            print file_name
            document = html.parse(file_name)

            movie = Movie.objects.create(
                url=SITE_ROOT + file_name.split('/')[-1] + '/',
                title=document.getroot().cssselect('.tytul.zloty')[0].text,
                info={
                    'description': '\n'.join(el.text for el in
                                             document.getroot().cssselect('.ps_body p'))})

            self.load_screenings(movie, document.getroot())

    def load_screenings(self, movie, root):
        elements = root.cssselect('.pokazy li')[1:] # first list element is a header
        for element in elements:
            parts = [(e.tail or '').strip() for e in element]
            hour, minute = parts[2].split('.')
            Screening.objects.create(
                movie=movie,
                date=datetime(2012, 10, int(parts[1].split(' ')[0]), int(hour), int(minute)),
                room=element.text.strip())
        
        
