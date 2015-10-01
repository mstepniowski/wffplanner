import codecs
import requests
import sys
from lxml import html


def get_movies():
    response = requests.get('http://wff.pl/filmy/2015')
    if not response.status_code / 100 == 2:
        sys.exit(1)

    document = html.fromstring(response.content)
    articles = document.cssselect('.movieItem article')
    for i, article in enumerate(articles):
        print article.cssselect('h1')[0].text
        output = codecs.open('data/%d.html' % i, 'w', encoding='utf-8')
        output.write(html.tostring(article))
        output.close()


if __name__ == '__main__':
    get_movies()
