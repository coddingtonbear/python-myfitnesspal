from myfitnesspal.base import MFPBase


class Day(MFPBase):
    def __init__(
        self,
        date,
        meals=None,
        goals=None,
        notes=None,
        water=None,
        exercises=None,
        complete=False,
    ):
        self._date = date
        self._meals = meals
        self._goals = goals
        self._notes = notes
        self._water = water
        self._exercises = exercises
        self._totals = None
        self._complete = complete

    def __getitem__(self, value):
        for meal in self._meals:
            if meal.name.lower() == value.lower():
                return meal
        raise KeyError(f"No meal named '{value}' exists for this date")

    def keys(self):
        keys = []
        for meal in self.meals:
            keys.append(meal.name)
        return keys

    @property
    def meals(self):
        return self._meals

    @property
    def complete(self):
        return self._complete

    @property
    def entries(self):
        for meal in self._meals:
            yield from meal.entries

    @property
    def totals(self):
        if self._totals is None:
            self._compute_totals()

        return self._totals

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

    @property
    def exercises(self):
        return self._exercises()

    def get_as_dict(self):
        return {m.name: m.get_as_list() for m in self.meals}

    def _compute_totals(self):
        totals = {}
        for entry in self.entries:
            for k, v in entry.nutrition_information.items():
                if k not in totals:
                    totals[k] = v
                else:
                    totals[k] += v
        self._totals = totals

    def __str__(self):
        date_str = self.date.strftime("%x")
        return f"{date_str} {self.totals}"
