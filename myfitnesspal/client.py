import os.path

import lxml.html
import requests

from myfitnesspal.day import Day
from myfitnesspal.entry import Entry
from myfitnesspal.meal import Meal


class Client(object):
    BASE_URL = 'http://www.myfitnesspal.com/'
    ABBREVIATIONS = {
        'carbs': 'carbohydrates',
    }

    def __init__(self, username, password):
        self.username = username
        self.password = password
        self.session = requests.Session()

    def _get_full_name(self, raw_name):
        name = raw_name.lower()
        if name not in self.ABBREVIATIONS:
            return name
        return self.ABBREVIATIONS[name]

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

    def _get_document_for_url(self, url):
        content = self._get_content_for_url(url).content

        return lxml.html.document_fromstring(content)

    def _build_field_list(self, tds):
        fields = ['name']
        for field in tds[1:]:
            fields.append(
                self._get_full_name(
                    field.text
                )
            )
        return fields

    def _get_meals(self, document):
        meals = []
        fields = None
        meal_headers = document.xpath("//tr[@class='meal_header']")

        for meal_header in meal_headers:
            tds = meal_header.findall('td')
            meal_name = tds[0].text.lower()
            if fields is None:
                fields = self._build_field_list(tds)
            this = meal_header
            entries = []

            while True:
                this = this.getnext()
                if not this.attrib.get('class') is None:
                    break
                columns = this.findall('td')
                name = columns[0].find('a').text.lower()
                nutrition = {}

                for n in range(1, len(columns)):
                    column = columns[n]
                    try:
                        nutr_name = fields[n]
                    except IndexError:
                        # This is the 'delete' button
                        continue
                    nutrition[nutr_name] = column.text

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

    def get_date(self, date):
        document = self._get_document_for_url(
            self._get_url_for_date(
                date
            )
        )

        meals = self._get_meals(document)
        totals = []
        goals = []

        day = Day(
            date=date,
            meals=meals,
            totals=totals,
            goals=goals,
        )

        return day
