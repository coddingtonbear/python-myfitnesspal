import re
from typing import Iterable, Optional

from myfitnesspal.base import MFPBase

from . import types


class Entry(MFPBase):
    """Stores information about a single entry."""

    def __init__(self, name: str, nutrition: types.NutritionDict):
        self._name = name
        self._nutrition = nutrition

        # split out quantity and measuring unit out of entry name
        regex = r"(?P<short_name>.+), (?P<quantity>\d[\d\.]*) (?P<unit>[\w\(\)]+)(?: \(.*\))?"
        match = re.search(regex, name)

        self._quantity: Optional[str] = None
        self._unit: Optional[str] = None
        self._short_name: Optional[str] = None
        if match:
            self._quantity = match.group("quantity")
            self._unit = match.group("unit")
            self._short_name = match.group("short_name")

    def __getitem__(self, value: str) -> float:
        return self.totals[value]

    def keys(self) -> Iterable[str]:
        return self.totals.keys()

    @property
    def name(self) -> str:
        """Name of the item."""
        return self._name.strip()

    @property
    def nutrition_information(self) -> types.NutritionDict:
        return self._nutrition

    @property
    def totals(self) -> types.NutritionDict:
        """Totals for the item."""
        return self.nutrition_information

    def get_as_dict(self) -> types.MealEntry:
        """Returns totals per-item as a dictionary."""
        return {
            "name": self.name,
            "nutrition_information": self.nutrition_information,
        }

    def __str__(self) -> str:
        return f"{self.name} {self.nutrition_information}"

    @property
    def short_name(self) -> Optional[str]:
        """Short name."""
        if self._short_name:
            return self._short_name.strip()
        return self._short_name

    @property
    def unit(self) -> Optional[str]:
        """Unit."""
        return self._unit

    @property
    def quantity(self) -> Optional[str]:
        """Quantity."""
        return self._quantity
