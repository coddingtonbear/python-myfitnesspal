import os.path

import requests

from myfitnesspal.day import Day
from myfitnesspal.entry import Entry
from myfitnesspal.meal import Meal


class Client(object):
    BASE_URL = 'http://www.myfitnesspal.com/'

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()

    def _get_url_for_date(self, date):
        return os.path.join(
            self.BASE_URL,
            'food/diary',
            self.username,
        ) + '?date=%s' % (
            date.strftime('%Y-%m-%d')
        )

    def _get_content_for_url(self, url):
        return self.session.get(url).content

    def get_date(self, date):
        url = self._get_url_for_date(date)
        content = self._get_content_for_url(url)

        meals = []
        totals = []
        goals = []

        day = Day(
            date=date,
            meals=meals,
            totals=totals,
            goals=goals,
        )

        return day
