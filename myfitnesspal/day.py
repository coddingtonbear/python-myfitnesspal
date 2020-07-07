import datetime
from typing import Callable, Dict, Generator, List, Optional

from myfitnesspal.base import MFPBase

from . import types
from .entry import Entry
from .exercise import Exercise
from .meal import Meal


class Day(MFPBase):
    def __init__(
        self,
        date: datetime.date,
        meals: Optional[List[Meal]] = None,
        goals: Dict[str, float] = None,
        notes: Callable[[], str] = None,
        water: Callable[[], float] = None,
        exercises: Callable[[], List[Exercise]] = None,
        complete: bool = False,
    ):
        self._date = date
        self._meals: List[Meal] = meals or []
        self._goals: Dict[str, float] = goals or {}
        self._notes = notes
        self._water = water
        self._exercises = exercises
        self._totals: Optional[Dict[str, float]] = None
        self._complete = complete

    def __getitem__(self, value: str) -> Meal:
        for meal in self._meals:
            if meal.name.lower() == value.lower():
                return meal
        raise KeyError(f"No meal named '{value}' exists for this date")

    def keys(self) -> List[str]:
        keys = []
        for meal in self.meals:
            keys.append(meal.name)
        return keys

    @property
    def meals(self) -> List[Meal]:
        return self._meals

    @property
    def complete(self) -> bool:
        return self._complete

    @property
    def entries(self) -> Generator[Entry, None, None]:
        for meal in self._meals:
            yield from meal.entries

    @property
    def totals(self) -> Dict[str, float]:
        if self._totals is None:
            self._compute_totals()

        assert self._totals is not None

        return self._totals

    @property
    def goals(self) -> Dict[str, float]:
        return self._goals

    @property
    def date(self) -> datetime.date:
        return self._date

    @property
    def notes(self) -> str:
        if not self._notes:
            return ""

        return self._notes()

    @property
    def water(self) -> float:
        if not self._water:
            return 0

        return self._water()

    @property
    def exercises(self) -> List[Exercise]:
        if not self._exercises:
            return []

        return self._exercises()

    def get_as_dict(self) -> Dict[str, List[types.MealEntry]]:
        return {m.name: m.get_as_list() for m in self.meals}

    def _compute_totals(self) -> None:
        totals: Dict[str, float] = {}
        for entry in self.entries:
            for k, v in entry.nutrition_information.items():
                if k not in totals:
                    totals[k] = v
                else:
                    totals[k] += v
        self._totals = totals

    def __str__(self) -> str:
        date_str = self.date.strftime("%x")
        return f"{date_str} {self.totals}"
