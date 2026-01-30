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
        self.source = 'Habr'

    def parse(self):
        response = requests.get(self._normalize_url(), headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36'
        })
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')

        articles_list = soup.find('div', class_='tm-articles-list')
        if not articles_list:
            return []

        result = []
        for article in articles_list.find_all('article'):
            try:
                h2 = article.find('h2')
                if not h2 or not h2.a:
                    continue

                title_elem = h2.a.find('span')
                if not title_elem:
                    title_elem = h2.a

                title = title_elem.text.strip() if title_elem else None
                if not title:
                    continue

                article_id = article.get('id')
                url = self._normalize_url(article_id) if article_id else None

                summary_elem = article.find('div', class_='article-formatted-body')
                summary = summary_elem.text.strip() if summary_elem else ''

                time_elem = article.find('time')
                if not time_elem or not time_elem.get('datetime'):
                    continue

                published_at = datetime.fromisoformat(time_elem.get('datetime'))

                result.append({
                    'title': title,
                    'url': url,
                    'summary': summary,
                    'source': self.source,
                    'published_at': published_at
                })
            except Exception as e:
                continue # Пропускаем статьи с ошибками парсинга

        return result

if __name__ == '__main__':
    pprint(HabrParser().parse())