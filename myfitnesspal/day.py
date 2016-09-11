from myfitnesspal.base import MFPBase


class Day(MFPBase):
    def __init__(self, date, meals=None, goals=None, notes=None, water=None):
        self._date = date
        self._meals = meals
        self._goals = goals
        self._notes = notes
        self._water = water

    def __getitem__(self, value):
        for meal in self._meals:
            if meal.name.lower() == value.lower():
                return meal
        raise KeyError("No meal named '%s' exists for this date" % value)

    def keys(self):
        keys = []
        for meal in self.meals:
            keys.append(meal.name)
        return keys

    @property
    def meals(self):
        return self._meals

    @property
    def entries(self):
        for meal in self._meals:
            for entry in meal.entries:
                yield entry

    @property
    def totals(self):
        nutrition = {}
        for entry in self.entries:
            for k, v in entry.nutrition_information.items():
                if k not in nutrition:
                    nutrition[k] = v
                else:
                    nutrition[k] += v

        return nutrition

    @property
    def goals(self):
        return self._goals

    @property
    def date(self):
        return self._date

    @property
    def notes(self):
        return self._notes()

    @property
    def water(self):
        return self._water()

    def get_as_dict(self):
        return dict(
            (m.name, m.get_as_list(), ) for m in self.meals
        )

    def __unicode__(self):
        return u'%s %s' % (
            self.date.strftime('%x'),
            self.totals,
        )
