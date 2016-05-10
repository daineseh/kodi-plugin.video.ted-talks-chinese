# -*- coding: utf8 -*-

from bs4 import BeautifulSoup
from collections import OrderedDict

import requests
import urlparse


BASE_URL = 'https://www.ted.com'
BUILD_URL = lambda x: urlparse.urljoin(BASE_URL, x).encode('utf8')


class Talk:
    def __init__(self, speaker = None, title = None,
                 url = None, thumb = None):
        self.speaker = self._to_str_type(speaker)
        self.title = self._to_str_type(title)
        self.thumb = self._to_str_type(thumb)
        self.url = self._to_str_type(url)

    def _to_str_type(self, value):
        if not value:
            return
        if isinstance(value, str):
            return value
        return value.encode('utf8')

    @property
    def speaker(self):
        return self.__speaker

    @speaker.setter
    def speaker(self, value):
        self.__speaker = value

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, value):
        self.__title = value

    @property
    def thumb(self):
        return self.__thumb

    @thumb.setter
    def thumb(self, value):
        self.__thumb = value

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, value):
        self.__url = value


class TedParser:
    def __init__(self, url = None):
        self.soup = None
        self.url = url if url else 'https://www.ted.com/talks?language=zh-tw'
        req = requests.get(self.url)
        self.soup = BeautifulSoup(req.text, 'html.parser') if req else None
        # Get next page
        next_tag = self.soup.find('a', 'pagination__next')
        self.next_page = BUILD_URL(next_tag.get('href')) if next_tag else ''
        if not self.next_page:
            self.last_page = ''
            return
        # Get last page
        last_tag = next_tag.find_previous_sibling('a')
        self.last_page = BUILD_URL(last_tag.get('href')) if last_tag else ''

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, value):
        self.__url = value

    @property
    def next_page(self):
        return self.__next_page

    @next_page.setter
    def next_page(self, value):
        self.__next_page = value

    @property
    def last_page(self):
        return self.__last_page

    @last_page.setter
    def last_page(self, value):
        self.__last_page = value

    def get_talks(self):
        talks = []
        for div_tag in self.soup.find_all('div', 'media media--sm-v'):
            tag_img = div_tag.find('img', ' thumb__image')
            img = tag_img.get('src')
            # Get higher pixel photo
            width = int(img.split('=')[-1]) * 2
            width_str = '=%d' % width
            eq_num = img.rfind('=')
            thumb = img[:eq_num] + width_str

            tag_h4 = div_tag.find('h4', 'h12 talk-link__speaker')
            speaker = tag_h4.string

            for tag_a in div_tag.find_all('a'):
                if not tag_a.string:
                    continue
                url = BUILD_URL(tag_a.get('href'))
                title = tag_a.string.strip()
            talks.append(Talk(speaker, title, url, thumb))

        return talks


if __name__ == '__main__':
    obj = TedParser()

