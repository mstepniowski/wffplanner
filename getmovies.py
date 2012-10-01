import codecs
import requests
from lxml import html


SITE_ROOT = 'http://www.wff.pl'


def alphabet():
    for x in range(ord('a'), ord('z')):
        yield chr(x)


def alphabetical_urls():
    yield SITE_ROOT + '/filmy/wszystkie/special/0/'
    for c in alphabet():
        yield SITE_ROOT + '/filmy/wszystkie/%s/0/' % c


def get_movie_urls(url, recurse=True):
    print 'get_movie_urls(%r, recurse=%r)' % (url, recurse)
    response = requests.get(url)
    if not response.status_code / 100 == 2:
        return []
        
    document = html.fromstring(response.content)
    urls = [SITE_ROOT + '/' + a.get('href')
            for a in document.cssselect('.nowina a:first-child')]

    is_there_submenu = len(document.cssselect('.podmenu.dolny')) >= 2
    print len(document.cssselect('.podmenu.dolny'))
    if is_there_submenu and recurse:
        submenu = document.cssselect('.podmenu.dolny')[0]
        next_urls = [SITE_ROOT + '/' + a.get('href')
                     for a in submenu.cssselect('a')
                     if a.get('class') != 'current']
        for fetch_url in next_urls:
            urls += get_movie_urls(fetch_url, recurse=False)
        
    return urls


def get_all_movie_urls():
    MOVIE_URLS = []
    
    try:
        for url in alphabetical_urls():
            MOVIE_URLS.extend(get_movie_urls(url))
    finally:
        output = file('urls.txt', 'w')
        for url in MOVIE_URLS:
            output.write(url + '\n')
        output.close()


def fetch_movie(url):
    print 'fetch_movie(%r)' % url
    response = requests.get(url)
    output = codecs.open('data/' + url.split('/')[-2], 'w', encoding='utf-8')
    output.write(response.content.decode('utf-8'))
    output.close()
