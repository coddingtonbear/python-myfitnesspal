from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional

from myfitnesspal.base import MFPBase
from myfitnesspal.types import FoodItemNutritionDict

from . import types
from .fooditemserving import FoodItemServing

if TYPE_CHECKING:
    from myfitnesspal.client import Client


class FoodItem(MFPBase):
    def __init__(
        self,
        mfp_id: int,
        name: str,
        brand: Optional[str],
        verified: bool,
        calories: float,
        details: Optional[FoodItemNutritionDict] = None,
        confirmations: Optional[int] = None,
        serving_sizes: Optional[List[types.ServingSizeDict]] = None,
        client: Optional["Client"] = None,
    ):
        self._mfp_id = mfp_id
        self._name = name
        self._brand = brand
        self._verified = verified
        self._calories = calories

        self._details: Optional[FoodItemNutritionDict] = None
        self._confirmations = confirmations
        self._serving_sizes = serving_sizes
        self._client = client

    def _load_nutrition_details(self):
        if self._details:
            return

        assert self._client

        details = self._client._get_food_item_details(self.mfp_id)

        self._details = details["nutrition"]
        self._confirmations = details["confirmations"]
        self._serving_sizes = details["serving_sizes"]

    @property
    def details(self) -> FoodItemNutritionDict:
        self._load_nutrition_details()
        assert self._details is not None

        return self._details

    @property
    def mfp_id(self) -> int:
        return self._mfp_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def brand(self) -> Optional[str]:
        return self._brand

    @property
    def verified(self) -> bool:
        return self._verified

    @property
    def serving(self) -> Optional[str]:
        self._load_nutrition_details()

        assert self._serving_sizes is not None

        for s in self._serving_sizes:
            if s["index"] == 0:
                return s["unit"]

        return None

    @property
    def calories(self) -> float:
        return self._calories

    @property
    def calcium(self) -> float:
        return self.details["calcium"]

    @property
    def carbohydrates(self) -> float:
        return self.details["carbohydrates"]

    @property
    def cholesterol(self) -> float:
        return self.details["cholesterol"]

    @property
    def fat(self) -> float:
        return self.details["fat"]

    @property
    def fiber(self) -> float:
        return self.details["fiber"]

    @property
    def iron(self) -> float:
        return self.details["iron"]

    @property
    def monounsaturated_fat(self) -> float:
        return self.details["monounsaturated_fat"]

    @property
    def polyunsaturated_fat(self) -> float:
        return self.details["polyunsaturated_fat"]

    @property
    def potassium(self) -> float:
        return self.details["potassium"]

    @property
    def protein(self) -> float:
        return self.details["protein"]

    @property
    def saturated_fat(self) -> float:
        return self.details["saturated_fat"]

    @property
    def sodium(self) -> float:
        return self.details["sodium"]

    @property
    def sugar(self) -> float:
        return self.details["sugar"]

    @property
    def trans_fat(self) -> float:
        return self.details["trans_fat"]

    @property
    def vitamin_a(self) -> float:
        return self.details["vitamin_a"]

    @property
    def vitamin_c(self) -> float:
        return self.details["vitamin_c"]

    @property
    def confirmations(self) -> int:
        self._load_nutrition_details()

        assert self._confirmations is not None

        return self._confirmations

    @property
    def servings(self) -> List[FoodItemServing]:
        self._load_nutrition_details()

        assert self._serving_sizes is not None

        servings: List[FoodItemServing] = []

        for s in self._serving_sizes:
            serving = FoodItemServing(
                s["id"],
                s["nutrition_multiplier"],
                s["value"],
                s["unit"],
                s["index"],
            )
            servings.append(serving)

        return servings

    def __str__(self) -> str:
        return f"{self.name} -- {self.brand}"
