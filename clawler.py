# -*- coding: utf8 -*-

from bs4 import BeautifulSoup
from collections import OrderedDict

import os
import re
import requests
import urlparse
import xbmc


BASE_URL = 'https://www.ted.com'
BUILD_URL = lambda x: urlparse.urljoin(BASE_URL, x).encode('utf8')

SORT_TABLE = OrderedDict([('最新', 'newest'),
                          ('最久', 'oldest'),
                          ('最受歡迎', 'popular'),
                          ('印象深刻', 'jaw-dropping'),
                          ('有趣', 'funny'),
                          ('說服力', 'persuasive'),
                          ('勇氣', 'courageous'),
                          ('聰明', 'ingenious'),
                          ('吸引', 'fascinating'),
                          ('鼓舞人心', 'inspiring'),
                          ('美感', 'beautiful'),
                          ('啟發性', 'informative')])

class TEDSub2SubRip:
    def __init__(self, ted_subs, intro_time = 0):
        self.ted_subs = ted_subs
        self.intro_time = intro_time
        self.statements = []
        self.__process_statements()

    def __srt_time(self, tst):
        """Format Time from TED Subtitles format to SRT time Format."""
        secs, mins, hours = ((tst / 1000) % 60), (tst / 60000), (tst / 3600000)
        right_srt_time = ("%02d:%02d:%02d,%02d" %
                           (int(hours), int(mins), int(secs), divmod(secs, 1)[1] * 1000))
        return right_srt_time

    def __process_statements(self):
        if not self.ted_subs.has_key('captions'):
            return

        for line, caption in enumerate(self.ted_subs.get('captions'), start=1):
            start = caption.get('startTime') + self.intro_time
            end = caption.get('duration') + start
            time_line = '%s --> %s' % (self.__srt_time(start), self.__srt_time(end))
            text_line = caption.get('content').encode('utf8')
            self.statements.append([str(line), time_line, text_line, '\n'])

    def reads(self):
        if not self.statements:
            return ''

        sub_content = ''
        for stat in self.statements:
            sub_content += '\n'.join(stat)
        return sub_content


class TEDSub2SubRipWrapper:
    def __init__(self, url):
        self.req = requests.get(url)
        if not self.req:
            return None
        self.__process()

    def __process(self):
        regex_intro = re.compile('"introDuration":(\d+\.?\d+)')
        regex_id = re.compile('"id":(\d+),')

        talk_id = regex_id.findall(self.req.text)[0]
        tc_sub_url = urlparse.urljoin('https://www.ted.com/talks/subtitles/id/', '%s/lang/%s' % (talk_id, 'zh-tw'))
        print(tc_sub_url)
        req = requests.get(tc_sub_url)
        if not self.req:
            return None

        intro_time = ((float(regex_intro.findall(self.req.text)[0]) + 1) * 1000)

        self.sub_obj = TEDSub2SubRip(req.json(), intro_time)

    def output(self, sub_path):
        with open(sub_path, 'w') as fp:
            fp.write(self.sub_obj.reads())


class Talk:
    def _to_str_type(self, value):
        if not value:
            return
        if isinstance(value, str):
            return value
        return value.encode('utf8')

    @property
    def posted(self):
        return self.__posted

    @posted.setter
    def posted(self, value):
        self.__posted = self._to_str_type(value)

    @property
    def speaker(self):
        return self.__speaker

    @speaker.setter
    def speaker(self, value):
        self.__speaker = self._to_str_type(value)

    @property
    def time(self):
        return self.__time

    @time.setter
    def time(self, value):
        self.__time = self._to_str_type(value)

    @property
    def title(self):
        return self.__title

    @title.setter
    def title(self, value):
        self.__title = self._to_str_type(value)

    @property
    def thumb(self):
        return self.__thumb

    @thumb.setter
    def thumb(self, value):
        self.__thumb = self._to_str_type(value)

    @property
    def url(self):
        return self.__url

    @url.setter
    def url(self, value):
        self.__url = self._to_str_type(value)


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

    @classmethod
    def page_number(cls, url):
        match = re.search("&page=(?P<id>\d+)", url)
        return match.group('id') if match else ''

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

            tag_span = div_tag.find('span', 'meta__val')
            posted = tag_span.string.strip()

            for tag_a in div_tag.find_all('a'):
                if not tag_a.string:
                    tag_span = tag_a.find('span', 'thumb__duration')
                    time = tag_span.string.strip()
                    continue
                url = BUILD_URL(tag_a.get('href'))
                title = tag_a.string.strip()

            talk = Talk()
            talk.speaker = speaker
            talk.title = title
            talk.time = time
            talk.url = url
            talk.thumb = thumb
            talk.posted = posted
            talks.append(talk)
        return talks


if __name__ == '__main__':
    obj = TedParser()

