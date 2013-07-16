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

    def __unicode__(self):
        return u'%s %s' % (
            self.name,
            self.nutrition_information,
        )
