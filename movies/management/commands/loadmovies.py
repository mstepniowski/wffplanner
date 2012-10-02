from datetime import datetime
from lxml import html

from django.core.management.base import BaseCommand

from movies.models import Movie, Screening


SITE_ROOT = 'http://www.wff.pl/filmy/'


class Command(BaseCommand):
    def handle(self, *file_names, **options):
        Movie.objects.all().delete()
        Screening.objects.all().delete()

        movies = {}
        for file_name in file_names:
            print file_name
            document = html.parse(file_name)
            movie, _ = Movie.objects.get_or_create(url=SITE_ROOT + file_name.split('/')[-1] + '/')
            movie.title = document.getroot().cssselect('.tytul.zloty')[0].text
            movie.info = self.load_extra_info(document.getroot())
            movie.collection_id = None
            movie.save()
            movies[movie.title] = movie
            self.load_screenings(movie, document.getroot())

        self.postprocess(movies)
    
    def load_extra_info(self, root):
        info = {'description': '\n'.join(el.text for el in
                                         root.cssselect('.ps_body p'))}
        rows = root.cssselect('.row')
        for row in rows:
            label = row.cssselect('span.zloty')
            if len(label) > 0 and label[0].text.strip() == 'Film w zestawie:':
                info['collection'] = row.cssselect('a')[0].text.strip()
        return info
    
    def load_screenings(self, movie, root):
        elements = root.cssselect('.pokazy li')[1:] # first list element is a header
        for element in elements:
            parts = [(e.tail or '').strip() for e in element]
            hour, minute = parts[2].split('.')
            Screening.objects.create(
                movie=movie,
                date=datetime(2012, 10, int(parts[1].split(' ')[0]), int(hour), int(minute)),
                room=element.text.strip())
        
    def postprocess(self, movies):
        for movie in movies.values():
            collection = movie.info.get('collection')
            if collection is not None and collection != movie.title:
                try:
                    movie.collection_id = movies[collection].url
                except KeyError:
                    print 'KeyError: ' + collection
                movie.save()
