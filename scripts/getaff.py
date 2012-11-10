import codecs
import requests
from lxml import html


SITE_ROOT = 'http://www.americanfilmfestival.pl'


def calendar_urls():
    return ['http://www.americanfilmfestival.pl/kalendarz.do?moje=false&dzien=%d' % day for day in range(13, 18+1)]


def get_movie_urls(url):
    response = requests.get(url)
    if not response.status_code / 100 == 2:
        return []
    document = html.fromstring(response.content)
    urls = [SITE_ROOT + '/' + a.get('href') for a in document.cssselect('a.op')]
    return urls


def get_all_movie_urls():
    result = []
    for url in calendar_urls():
        result.extend(get_movie_urls(url))
    return set(result)


def fetch_movie(url):
    print 'fetch_movie(%r)' % url
    response = requests.get(url)
    output = codecs.open('data/aff/' + url[-4:] + '.html', 'w', encoding='utf-8')
    output.write(response.content.decode('utf-8'))
    output.close()
