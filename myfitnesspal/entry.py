import re

from myfitnesspal.base import MFPBase


class Entry(MFPBase):
    def __init__(self, name, nutrition):
        self._name = name
        self._nutrition = nutrition
        
        #split out quantity and measuring unit out of entry name
        regex = r'(?P<short_name>.+), (?P<quantity>\d[\d\.]*) (?P<unit>[\w\(\)]+)(?: \(.*\))?'
        match = re.search(regex, name)

        self._quantity = None
        self._unit = None
        self._short_name = None
        if match:
            self._quantity = match.group('quantity')
            self._unit = match.group('unit')
            self._short_name = match.group('short_name')

    def __getitem__(self, value):
        return self.totals[value]

    def keys(self):
        return self.totals.keys()

    @property
    def name(self):
        return self._name.strip()

    @property
    def nutrition_information(self):
        return self._nutrition

    @property
    def totals(self):
        return self.nutrition_information


    def get_as_dict(self):
        return {
            'name': self.name,
            'nutrition_information': self.nutrition_information,
        }

    def __unicode__(self):
        return u'%s %s' % (
            self.name,
            self.nutrition_information,
        )

    @property
    def short_name(self):
        if self._short_name:
            return self._short_name.strip()
        return self._short_name

    @property
    def unit(self):
        return self._unit

    @property
    def quantity(self):
        return self._quantity
