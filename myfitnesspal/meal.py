from myfitnesspal.base import MFPBase


class Meal(MFPBase):
    def __init__(self, name, entries):
        self._name = name
        self._entries = entries

    @property
    def entries(self):
        return self._entries

    @property
    def name(self):
        return self._name

    def __unicode__(self):
        return u'%s' % (
            self.name,
        )
