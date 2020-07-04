import datetime
import os

import pytest

from myfitnesspal import Client

from .base import MFPTestCase


class TestIntegration(MFPTestCase):
    @classmethod
    def setUpClass(cls):
        try:
            username = os.environ["MFP_INTEGRATION_TESTING_USERNAME"]
            password = os.environ["MFP_INTEGRATION_TESTING_PASSWORD"]
        except KeyError:
            pytest.skip("Integration testing account not set in this environment.")
            return

        client = Client(username, password,)

        day_with_known_entries = datetime.date(2020, 7, 4)

        cls.day = client.get_date(day_with_known_entries)

    def test_get_exercises_dict(self):
        expected_exercise_dicts = [
            [
                {
                    "name": "Rowing, stationary, very vigorous effort",
                    "nutrition_information": {
                        "minutes": 30.0,
                        "calories burned": 408.0,
                    },
                }
            ],
            [
                {
                    "name": "Squat",
                    "nutrition_information": {
                        "sets": 5.0,
                        "reps/set": 5.0,
                        "weight/set": 225.0,
                    },
                }
            ],
        ]
        actual_exercises = [exercise.get_as_list() for exercise in self.day.exercises]

        assert actual_exercises == expected_exercise_dicts

    def test_get_day_meal_dict(self):
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

        actual_meal_dict = self.day.get_as_dict()

        assert actual_meal_dict == expected_meal_dict
