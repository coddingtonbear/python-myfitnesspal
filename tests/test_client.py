import copy
import datetime
from collections import OrderedDict
from unittest.mock import patch

from measurement.measures import Energy, Weight

from myfitnesspal import Client

from .base import MFPTestCase


class TestClient(MFPTestCase):
    def setUp(self):
        self.arbitrary_username = "alpha"
        self.arbitrary_password = "beta"
        self.arbitrary_date1 = datetime.date(2015, 4, 20)
        self.arbitrary_date2 = datetime.date(2015, 4, 28)
        self.client = Client(
            self.arbitrary_username, self.arbitrary_password, login=False
        )
        super().setUp()

    def test_get_measurement_ids(self):
        document = self.get_html_document("measurements.html")
        actual_ids = self.client._get_measurement_ids(document)

        expected_ids = {
            "Weight": 1,
            "Body Fat": 91955886,
            "Butt": 92738807,
            "Bicep": 92738811,
            "Quad": 92738815,
            "Mid Section": 92738819,
            "Shoulders": 92738861,
        }

        self.assertEqual(
            expected_ids,
            actual_ids,
        )

    def test_get_meals(self):
        document = self.get_html_document("diary.html")
        meals = self.client._get_meals(document)

        self.assertEqual(
            len(meals),
            4,
        )

    def test_get_measurements(self):
        with patch.object(self.client, "_get_document_for_url") as get_doc:
            get_doc.return_value = self.get_html_document("measurements.html")
            actual_measurements = self.client.get_measurements(
                "Body Fat",
                self.arbitrary_date1,
                self.arbitrary_date2,
            )

        expected_measurements = OrderedDict(
            [
                (datetime.date(2015, 4, 28), 19.2),
                (datetime.date(2015, 4, 27), 19.2),
                (datetime.date(2015, 4, 26), 19.0),
                (datetime.date(2015, 4, 25), 18.7),
                (datetime.date(2015, 4, 23), 18.7),
                (datetime.date(2015, 4, 22), 18.4),
                (datetime.date(2015, 4, 21), 18.9),
                (datetime.date(2015, 4, 20), 19.1),
            ]
        )

        self.assertEqual(
            expected_measurements,
            actual_measurements,
        )

    def test_get_day_unit_unaware(self):
        self.client.unit_aware = False

        with patch.object(self.client, "_get_document_for_url") as get_doc:
            get_doc.return_value = self.get_html_document("diary.html")
            day = self.client.get_date(self.arbitrary_date1)

        expected_dict = {
            "lunch": [],
            "breakfast": [
                {
                    "nutrition_information": {
                        "sodium": 380,
                        "carbohydrates": 44,
                        "calories": 240,
                        "fat": 6,
                        "sugar": 8,
                        "protein": 10,
                    },
                    "name": "Dave's Killer Bread - Blues Bread, 2 slice",
                },
                {
                    "nutrition_information": {
                        "sodium": 100,
                        "carbohydrates": 0,
                        "calories": 100,
                        "fat": 11,
                        "sugar": 0,
                        "protein": 0,
                    },
                    "name": (
                        "Earth Balance - "
                        "Natural Buttery Spread - Original, 1 tbsp (14g)"
                    ),
                },
            ],
            "dinner": [
                {
                    "nutrition_information": {
                        "sodium": 5,
                        "carbohydrates": 8,
                        "calories": 288,
                        "fat": 0,
                        "sugar": 0,
                        "protein": 0,
                    },
                    "name": "Wine - Pinot Noir Wine, 12 oz",
                },
                {
                    "nutrition_information": {
                        "sodium": 1166,
                        "carbohydrates": 64,
                        "calories": 690,
                        "fat": 48,
                        "sugar": 14,
                        "protein": 30,
                    },
                    "name": "Generic - Baked Macaroni and Cheese, 14 grams",
                },
            ],
            "snacks": [
                {
                    "nutrition_information": {
                        "sodium": 80,
                        "carbohydrates": 3,
                        "calories": 170,
                        "fat": 2,
                        "sugar": 2,
                        "protein": 36,
                    },
                    "name": "Mrm - Dutch Chocolate Whey Protein, 2 scoop",
                },
                {
                    "nutrition_information": {
                        "sodium": 338,
                        "carbohydrates": 36,
                        "calories": 203,
                        "fat": 6,
                        "sugar": 34,
                        "protein": 2,
                    },
                    "name": "Drinks - Almond Milk (Vanilla), 18 oz",
                },
                {
                    "nutrition_information": {
                        "sodium": 0,
                        "carbohydrates": 48,
                        "calories": 588,
                        "fat": 0,
                        "sugar": 0,
                        "protein": 0,
                    },
                    "name": (
                        "Dogfish Head 90 Minute Ipa - " "Beer, India Pale Ale, 24 oz"
                    ),
                },
            ],
        }
        actual_dict = day.get_as_dict()

        self.assertEqual(
            expected_dict,
            actual_dict,
        )
        self.assertEqual(
            day.date,
            self.arbitrary_date1,
        )
        self.assertEqual(
            day.complete,
            False,
        )
        self.assertEqual(
            day.goals,
            {
                "calories": 2500,
                "carbohydrates": 343,
                "fat": 84,
                "protein": 93,
                "sodium": 2500,
                "sugar": 50,
            },
        )
        self.assertEqual(
            day.totals,
            {
                "calories": 2279,
                "carbohydrates": 203,
                "fat": 73,
                "protein": 78,
                "sodium": 2069,
                "sugar": 58,
            },
        )

    def test_get_day(self):
        self.client.unit_aware = True

        with patch.object(self.client, "_get_document_for_url") as get_doc:
            get_doc.return_value = self.get_html_document("diary.html")
            day = self.client.get_date(self.arbitrary_date1)

        expected_dict = {
            "lunch": [],
            "breakfast": [
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=380),
                        "carbohydrates": Weight(g=44),
                        "calories": Energy(Calorie=240),
                        "fat": Weight(g=6),
                        "sugar": Weight(g=8),
                        "protein": Weight(g=10),
                    },
                    "name": "Dave's Killer Bread - Blues Bread, 2 slice",
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=100),
                        "carbohydrates": Weight(g=0),
                        "calories": Energy(Calorie=100),
                        "fat": Weight(g=11),
                        "sugar": Weight(g=0),
                        "protein": Weight(g=0),
                    },
                    "name": (
                        "Earth Balance - "
                        "Natural Buttery Spread - Original, 1 tbsp (14g)"
                    ),
                },
            ],
            "dinner": [
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=5),
                        "carbohydrates": Weight(g=8),
                        "calories": Energy(Calorie=288),
                        "fat": Weight(g=0),
                        "sugar": Weight(g=0),
                        "protein": Weight(g=0),
                    },
                    "name": "Wine - Pinot Noir Wine, 12 oz",
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=1166),
                        "carbohydrates": Weight(g=64),
                        "calories": Energy(Calorie=690),
                        "fat": Weight(g=48),
                        "sugar": Weight(g=14),
                        "protein": Weight(g=30),
                    },
                    "name": "Generic - Baked Macaroni and Cheese, 14 grams",
                },
            ],
            "snacks": [
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=80),
                        "carbohydrates": Weight(g=3),
                        "calories": Energy(Calorie=170),
                        "fat": Weight(g=2),
                        "sugar": Weight(g=2),
                        "protein": Weight(g=36),
                    },
                    "name": "Mrm - Dutch Chocolate Whey Protein, 2 scoop",
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=338),
                        "carbohydrates": Weight(g=36),
                        "calories": Energy(Calorie=203),
                        "fat": Weight(g=6),
                        "sugar": Weight(g=34),
                        "protein": Weight(g=2),
                    },
                    "name": "Drinks - Almond Milk (Vanilla), 18 oz",
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=0),
                        "carbohydrates": Weight(g=48),
                        "calories": Energy(Calorie=588),
                        "fat": Weight(g=0),
                        "sugar": Weight(g=0),
                        "protein": Weight(g=0),
                    },
                    "name": (
                        "Dogfish Head 90 Minute Ipa - " "Beer, India Pale Ale, 24 oz"
                    ),
                },
            ],
        }
        actual_dict = day.get_as_dict()

        self.assertEqual(
            expected_dict,
            actual_dict,
        )
        self.assertEqual(
            day.date,
            self.arbitrary_date1,
        )
        self.assertEqual(
            day.complete,
            False,
        )
        self.assertEqual(
            day.goals,
            {
                "calories": Energy(Calorie=2500),
                "carbohydrates": Weight(g=343),
                "fat": Weight(g=84),
                "protein": Weight(g=93),
                "sodium": Weight(mg=2500),
                "sugar": Weight(g=50),
            },
        )
        self.assertEqual(
            day.totals,
            {
                "calories": Energy(Calorie=2279),
                "carbohydrates": Weight(g=203),
                "fat": Weight(g=73),
                "protein": Weight(g=78),
                "sodium": Weight(mg=2069),
                "sugar": Weight(g=58),
            },
        )

    def test_get_day_get_totals_multiple_times(self):
        # Given: A `day` with information unit aware
        self.client.unit_aware = True
        with patch.object(self.client, "_get_document_for_url") as get_doc:
            get_doc.return_value = self.get_html_document("diary.html")
            day = self.client.get_date(self.arbitrary_date1)

        # When: Getting `totals` multiple times
        totals_1 = copy.deepcopy(day.totals)
        totals_2 = copy.deepcopy(day.totals)

        # Then: `totals` remain the same
        self.assertEqual(totals_1, totals_2)

    def test_get_exercise(self):
        with patch.object(self.client, "_get_document_for_url") as get_doc:
            get_doc.return_value = self.get_html_document("exercise.html")
            day = self.client._get_exercises(self.arbitrary_date1)

        # The returned object should be an array of length 2
        self.assertEqual(
            len(day),
            2,
        )

        # The first object of the array should be our cardio
        self.assertEqual(
            day[0].name,
            "cardiovascular",
        )

        # The second object should be our strength training
        self.assertEqual(
            day[1].name,
            "strength training",
        )

        expected_cardio = [
            {
                "name": "Yoga",
                "nutrition_information": {"minutes": 20, "calories burned": 62},
            },
            {
                "name": "Swimming, breaststroke, general",
                "nutrition_information": {"minutes": 10, "calories burned": 124},
            },
            {
                "name": "Running (jogging), 8 mph (7.5 min mile)",
                "nutrition_information": {"minutes": 20, "calories burned": 335},
            },
        ]
        actual_cardio = day[0].get_as_list()

        expected_strength = [
            {
                "name": "Bench Press, Barbell",
                "nutrition_information": {"sets": 3, "reps/set": 10, "weight/set": 30},
            },
            {
                "name": "Pull Ups (pull-ups)",
                "nutrition_information": {"sets": 3, "reps/set": 8, "weight/set": None},
            },
        ]

        actual_strength = day[1].get_as_list()

        self.assertEqual(
            expected_cardio,
            actual_cardio,
        )

        self.assertEqual(
            expected_strength,
            actual_strength,
        )

    def test_get_completed_day(self):
        with patch.object(self.client, "_get_document_for_url") as get_doc:
            get_doc.return_value = self.get_html_document("completed_diary.html")
            day = self.client.get_date(self.arbitrary_date1)

        self.assertEqual(
            day.complete,
            True,
        )
