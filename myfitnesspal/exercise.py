from myfitnesspal.base import MFPBase


class Exercise(MFPBase):
    def __init__(self, name, entries):
        self._name = name
        self._entries = entries

    def __getitem__(self, value):
        if not isinstance(value, int):
            raise ValueError("Index must be an integer")
        return self.entries[value]

    def __len__(self):
        return len(self.entries)

    @property
    def entries(self):
        return self._entries

    @property
    def name(self):
        return self._name

    def get_as_list(self):
        return [e.get_as_dict() for e in self.entries]

    def __str__(self):
        return self.name.title()
