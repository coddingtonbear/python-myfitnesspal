from typing import List

from myfitnesspal.base import MFPBase
from myfitnesspal.types import NutritionDict

from . import types
from .entry import Entry


class Meal(MFPBase):
    """Stores information about a particular meal."""

    def __init__(self, name: str, entries: List[Entry]):
        self._name = name
        self._entries = entries

    def __getitem__(self, value: int) -> Entry:
        """Returns a particular entry for thsi meal."""
        if not isinstance(value, int):
            raise ValueError("Index must be an integer")
        return self.entries[value]

    def __len__(self) -> int:
        return len(self.entries)

    @property
    def entries(self) -> List[Entry]:
        """Entries for this meal."""
        return self._entries

    @property
    def name(self) -> str:
        """Name of this meal."""
        return self._name

    @property
    def totals(self) -> NutritionDict:
        """Nutrition totals for all entries for this meal."""
        nutrition = {}
        for entry in self.entries:
            for k, v in entry.nutrition_information.items():
                if k not in nutrition:
                    nutrition[k] = v
                else:
                    nutrition[k] += v

        return nutrition

    def get_as_list(self) -> List[types.MealEntry]:
        return [e.get_as_dict() for e in self.entries]

    def __str__(self) -> str:
        return f"{self.name.title()} {self.totals}"
