from myfitnesspal.base import MFPBase


class Entry(MFPBase):
    def __init__(self, name, nutrition):
        self._name = name
        self._nutrition = nutrition

    @property
    def name(self):
        return self._name

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
