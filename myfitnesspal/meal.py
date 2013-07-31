from myfitnesspal.base import MFPBase


class Meal(MFPBase):
    def __init__(self, name, entries):
        self._name = name
        self._entries = entries

    def __getitem__(self, value):
        if not isinstance(value, int):
            raise ValueError('Index must be an integer')
        return self.entries[value]

    def __len__(self):
        return len(self.entries)

    @property
    def entries(self):
        return self._entries

    @property
    def name(self):
        return self._name

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

    def get_as_list(self):
        return [e.get_as_dict() for e in self.entries]

    def __unicode__(self):
        return u'%s %s' % (
            self.name.title(),
            self.totals
        )
