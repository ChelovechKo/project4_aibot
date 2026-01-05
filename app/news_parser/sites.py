from abc import ABC
from datetime import datetime
from pprint import pprint

import requests
from bs4 import BeautifulSoup


class SiteParser(ABC):
    def __init__(self, url: str, articles_path: str=''):
        self.base_url = url
        self.articles_url = articles_path

    def parse(self):
        raise NotImplementedError

    def _normalize_url(self, url: str=''):
        return self.base_url + self.articles_url + url

class HabrParser(SiteParser):
    def __init__(self):
        super().__init__('https://habr.com/', 'ru/articles/')
        self.source = 'habr'

    def parse(self):
        response = requests.get(self._normalize_url(), headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
        })
        soup = BeautifulSoup(response.text, 'html.parser')
        return [
            {
                'title': article.find('h2').a.span.text,
                'url': self._normalize_url(article.get('id')),
                'published_at': datetime.fromisoformat(article.find('time').get('datetime')),
                'summary': article.find('div', class_='article-formatted-body').text,
                'source': self.source
            } for article in soup.find('div', class_ = 'tm-articles-list').find_all('article')
        ]

pprint(HabrParser().parse())