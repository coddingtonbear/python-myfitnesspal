from myfitnesspal.base import MFPBase


class Day(MFPBase):
    def __init__(self, date, meals=None, totals=None, goals=None):
        self._date = date
        self._meals = meals
        self._totals = totals
        self._goals = goals

    @property
    def meals(self):
        return self._meals

    @property
    def entries(self):
        for meal in self._meals:
            for entry in meal:
                yield entry

    @property
    def totals(self):
        return self._totals

    @property
    def goals(self):
        return self._goals

    @property
    def date(self):
        return self._date

    def __unicode__(self):
        return u'%s %s' % (
            self.date.strftime('%Y-%m-%d'),
            self.totals,
        )
