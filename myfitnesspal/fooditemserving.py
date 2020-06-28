from myfitnesspal.base import MFPBase


class FoodItemServing(MFPBase):
    def __init__(self, serving_id, nutrition_multiplier, value, unit, index):
        self._serving_id = serving_id
        self._nutrition_multiplier = nutrition_multiplier
        self._value = value
        self._unit = unit
        self._index = index

    @property
    def serving_id(self):
        return self._serving_id

    @property
    def nutrition_multiplier(self):
        return self._nutrition_multiplier

    @property
    def value(self):
        return self._value

    @property
    def unit(self):
        return self._unit

    @property
    def index(self):
        return self._index

    def __str__(self):
        return f"{self.value:.2f} x {self.unit}"
