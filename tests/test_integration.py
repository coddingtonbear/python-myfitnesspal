import datetime
import os

import pytest

from myfitnesspal import Client

from .base import MFPTestCase


class TestIntegration(MFPTestCase):
    def setUp(self):
        try:
            self._username = os.environ["MFP_INTEGRATION_TESTING_USERNAME"]
            self._password = os.environ["MFP_INTEGRATION_TESTING_PASSWORD"]
        except KeyError:
            pytest.skip("Integration testing account not set in this environment.")
            return

        self.client = Client(self._username, self._password,)

    def test_get_day(self):
        day_with_known_entries = datetime.date(2020, 7, 4)

        day = self.client.get_date(day_with_known_entries)

        expected_meal_dict = {
            "breakfast": [
                {
                    "name": "Whole Foods - Juevos Rancheros, 2 cup",
                    "nutrition_information": {
                        "calories": 480,
                        "carbohydrates": 84,
                        "fat": 2,
                        "protein": 28,
                        "sodium": 2000,
                        "sugar": 4,
                    },
                }
            ],
            "lunch": [
                {
                    "name": "Trillium - Impossible Burger, 1 Burger",
                    "nutrition_information": {
                        "calories": 410,
                        "carbohydrates": 61,
                        "fat": 13,
                        "protein": 15,
                        "sodium": 780,
                        "sugar": 4,
                    },
                }
            ],
            "dinner": [
                {
                    "name": "Morrisons - Vegetarian Lasagne, 800 g",
                    "nutrition_information": {
                        "calories": 832,
                        "carbohydrates": 93,
                        "fat": 36,
                        "protein": 31,
                        "sodium": 3600,
                        "sugar": 30,
                    },
                }
            ],
            "snacks": [],
        }

        actual_meal_dict = day.get_as_dict()

        assert actual_meal_dict == expected_meal_dict
