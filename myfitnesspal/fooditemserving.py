from myfitnesspal.base import MFPBase


class FoodItemServing(MFPBase):
    def __init__(
        self,
        serving_id: str,
        nutrition_multiplier: float,
        value: float,
        unit: str,
        index: int,
    ):
        self._serving_id = serving_id
        self._nutrition_multiplier = nutrition_multiplier
        self._value = value
        self._unit = unit
        self._index = index

    @property
    def serving_id(self) -> str:
        return self._serving_id

    @property
    def nutrition_multiplier(self) -> float:
        return self._nutrition_multiplier

    @property
    def value(self) -> float:
        return self._value

    @property
    def unit(self) -> str:
        return self._unit

    @property
    def index(self) -> int:
        return self._index

    def __str__(self) -> str:
        return f"{self.value:.2f} x {self.unit}"
