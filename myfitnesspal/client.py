import datetime
import os.path
import re

import lxml.html
from measurement.measures import Energy, Weight, Volume
import requests

from myfitnesspal.base import MFPBase
from myfitnesspal.day import Day
from myfitnesspal.entry import Entry
from myfitnesspal.meal import Meal


class Client(MFPBase):
    BASE_URL = 'http://www.myfitnesspal.com/'
    BASE_URL_SECURE = 'https://www.myfitnesspal.com/'
    LOGIN_PATH = 'account/login'
    ABBREVIATIONS = {
        'carbs': 'carbohydrates',
    }
    DEFAULT_MEASURE_AND_UNIT = {
        'calories': (Energy, 'Calorie'),
        'carbohydrates': (Weight, 'g'),
        'fat': (Weight, 'g'),
        'protein': (Weight, 'g'),
        'sodium': (Weight, 'mg'),
        'sugar': (Weight, 'g'),
    }

    def __init__(self, username, password, login=True, unit_aware=False):
        self.username = username
        self.password = password
        self.unit_aware = unit_aware

        self.session = requests.Session()
        if login:
            self._login()

    def _login(self):
        login_url = os.path.join(self.BASE_URL_SECURE, self.LOGIN_PATH)
        document = self._get_document_for_url(login_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath(
            "(//input[@name='utf8']/@value)[1]"
        )[0]

        result = self.session.post(
            login_url,
            data={
                'utf8': utf8_field,
                'authenticity_token': authenticity_token,
                'username': self.username,
                'password': self.password,
            }
        )
        if 'Incorrect username or password' in result.content:
            raise ValueError(
                "Incorrect username or password."
            )

    def _get_full_name(self, raw_name):
        name = raw_name.lower()
        if name not in self.ABBREVIATIONS:
            return name
        return self.ABBREVIATIONS[name]

    def _get_url_for_date(self, date, username):
        return os.path.join(
            self.BASE_URL,
            'food/diary',
            username,
        ) + '?date=%s' % (
            date.strftime('%Y-%m-%d')
        )

    def _get_content_for_url(self, url):
        return self.session.get(url).content.decode('utf8')

    def _get_document_for_url(self, url):
        content = self._get_content_for_url(url)

        return lxml.html.document_fromstring(content)

    def _get_measurement(self, name, value):
        if not self.unit_aware:
            return value
        measure, kwarg = self.DEFAULT_MEASURE_AND_UNIT[name]
        return measure(**{kwarg: value})

    def _get_numeric(self, string):
        return int(re.sub(r'[^\d.]+', '', string))

    def _get_fields(self, document):
        meal_header = document.xpath("//tr[@class='meal_header']")[0]
        tds = meal_header.findall('td')
        fields = ['name']
        for field in tds[1:]:
            fields.append(
                self._get_full_name(
                    field.text
                )
            )
        return fields

    def _get_goals(self, document):
        total_header = document.xpath("//tr[@class='total']")[0]
        goal_header = total_header.getnext()  # The following TR contains goals
        columns = goal_header.findall('td')

        fields = self._get_fields(document)

        nutrition = {}
        for n in range(1, len(columns)):
            column = columns[n]
            try:
                nutr_name = fields[n]
            except IndexError:
                # This is the 'delete' button
                continue
            value = self._get_numeric(column.text)
            nutrition[nutr_name] = self._get_measurement(nutr_name, value)

        return nutrition

    def _get_meals(self, document):
        meals = []
        fields = None
        meal_headers = document.xpath("//tr[@class='meal_header']")

        for meal_header in meal_headers:
            tds = meal_header.findall('td')
            meal_name = tds[0].text.lower()
            if fields is None:
                fields = self._get_fields(document)
            this = meal_header
            entries = []

            while True:
                this = this.getnext()
                if not this.attrib.get('class') is None:
                    break
                columns = this.findall('td')

                # When viewing a friend's diary, the HTML entries containing the
                # actual food log entries are different: they don't contain an
                # embedded <a/> element but rather the food name directly.
                if columns[0].find('a') is None:
                    name = columns[0].text.strip()
                else:
                    name = columns[0].find('a').text

                nutrition = {}

                for n in range(1, len(columns)):
                    column = columns[n]
                    try:
                        nutr_name = fields[n]
                    except IndexError:
                        # This is the 'delete' button
                        continue
                    value = self._get_numeric(column.text)
                    nutrition[nutr_name] = self._get_measurement(
                        nutr_name,
                        value
                    )

                entries.append(
                    Entry(
                        name,
                        nutrition,
                    )
                )

            meals.append(
                Meal(
                    meal_name,
                    entries,
                )
            )

        return meals

    def get_date(self, *args, **kwargs):
        if len(args) == 3:
            date = datetime.date(
                int(args[0]),
                int(args[1]),
                int(args[2]),
            )
        elif len(args) == 1 and isinstance(args[0], datetime.date):
            date = args[0]
        else:
            raise ValueError(
                'get_date accepts either a single datetime or date instance, '
                'or three integers representing year, month, and day '
                'respectively.'
            )
        document = self._get_document_for_url(
            self._get_url_for_date(
                date,
                kwargs.get('username', self.username)
            )
        )

        meals = self._get_meals(document)
        goals = self._get_goals(document)
        notes = self._get_notes(document)
        water = self._get_water(document)

        day = Day(
            date=date,
            meals=meals,
            goals=goals,
            notes=notes,
            water=water
        )

        return day

    def _get_notes(self, document):
        notes_header = document.xpath("//p[@class='note']")[0]
        header_text = [notes_header.text] if notes_header.text else []
        lines = header_text + map(lambda x: x.tail, notes_header)
        return '\n'.join([l.strip() for l in lines])

    def _get_water(self, document):
        water_header = document.xpath("//div[@class='water-counter']/p/a")[0]
        try:
            cups = int(water_header.tail.strip())
            if self.unit_aware:
                return Volume(us_cup=cups)
            return cups
        except (ValueError, TypeError):
            return None

    def __unicode__(self):
        return u'MyFitnessPal Client for %s' % self.username
