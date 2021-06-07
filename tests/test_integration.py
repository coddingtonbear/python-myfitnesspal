import datetime
import os

import pytest

from myfitnesspal import Client

from .base import MFPTestCase


class TestIntegration(MFPTestCase):
    client: Client

    @classmethod
    def setUpClass(cls):
        try:
            username = os.environ["MFP_INTEGRATION_TESTING_USERNAME"]
            password = os.environ["MFP_INTEGRATION_TESTING_PASSWORD"]
        except KeyError:
            pytest.skip("Integration testing account not set in this environment.")
            return

        cls.client = Client(
            username,
            password,
        )

        day_with_known_entries = datetime.date(2020, 7, 4)

        cls.day = cls.client.get_date(day_with_known_entries)

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

    def test_get_notes(self):
        expected_note = "Epstein didn't kill himself"
        actual_note = self.day.notes

        assert expected_note == actual_note

    def test_get_water(self):
        expected_water = 480.0
        actual_water = self.day.water

        assert expected_water == actual_water

    def test_search_results(self):
        results = self.client.get_food_search_results("Tortilla Chips -- Juanita's")

        # Don't assert that we get a particular match,
        # just make sure that we receive items
        # that happen to have an mfp_id; we can't
        # really know how the search results might
        # change in the future

        assert len(results) > 0
        for result in results:
            assert isinstance(result.mfp_id, int)

        # This is just to assert that we _do_ try
        # to load extra nutrition information on-access
        assert results[0].sodium > 0

    def test_get_food_item_details(self):
        juanitas_tortilla_chips_mfp_id = 63384601972733

        result = self.client.get_food_item_details(juanitas_tortilla_chips_mfp_id)

        assert result.mfp_id == juanitas_tortilla_chips_mfp_id
