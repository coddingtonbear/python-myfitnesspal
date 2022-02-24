from typing import List

from myfitnesspal.base import MFPBase

from . import types
from .entry import Entry


class Exercise(MFPBase):
    """Shows information about your exercise."""

    def __init__(self, name: str, entries: List[Entry]):
        self._name = name
        self._entries = entries

    def __getitem__(self, value: int) -> Entry:
        """Returns a particular entry."""
        if not isinstance(value, int):
            raise ValueError("Index must be an integer")
        return self.entries[value]

    def __len__(self) -> int:
        return len(self.entries)

    @property
    def entries(self) -> List[Entry]:
        """List of entries."""
        return self._entries

    @property
    def name(self) -> str:
        """Name of exercise."""
        return self._name

    def get_as_list(self) -> List[types.MealEntry]:
        """Returns exercises as a list of dictionaries."""
        return [e.get_as_dict() for e in self.entries]

    def __str__(self) -> str:
        return self.name.title()
