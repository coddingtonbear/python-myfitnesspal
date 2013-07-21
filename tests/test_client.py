import datetime

from measurement.measures import Energy, Weight
import mimic

from myfitnesspal import Client

from .base import MFPTestCase


class TestClient(MFPTestCase):
    def setUp(self):
        self.arbitrary_username = 'alpha'
        self.arbitrary_password = 'beta'
        self.arbitrary_date = datetime.date(2013,3,2)
        self.client = Client(
            self.arbitrary_username,
            self.arbitrary_password,
            login=False
        )
        super(TestClient, self).setUp()

    def _stub_response_document(self, filename):
        self.mimic.stub_out_with_mock(
            self.client,
            '_get_document_for_url'
        )
        self.client._get_document_for_url(
            mimic.IgnoreArg()
        ).and_return(
            self.get_html_document(
                filename
            )
        )

    def test_get_meals(self):
        document = self.get_html_document('2013-07-13.html')
        meals = self.client._get_meals(document)

        self.assertEquals(
            len(meals),
            4,
        )

    def test_get_day(self):
        self._stub_response_document('2013-07-13.html')

        self.mimic.replay_all()

        day = self.client.get_date(self.arbitrary_date)

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
                        "protein": Weight(g=10)
                    },
                    "name": "Dave's Killer Bread - Blues Bread, 2 slice"
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=100),
                        "carbohydrates": Weight(g=0),
                        "calories": Energy(Calorie=100),
                        "fat": Weight(g=11),
                        "sugar": Weight(g=0),
                        "protein": Weight(g=0)
                    },
                    "name": (
                        "Earth Balance - "
                        "Natural Buttery Spread - Original, 1 tbsp (14g)"
                    )
                }
            ],
            "dinner": [
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=5),
                        "carbohydrates": Weight(g=8),
                        "calories": Energy(Calorie=288),
                        "fat": Weight(g=0),
                        "sugar": Weight(g=0),
                        "protein": Weight(g=0)
                    },
                    "name": "Wine - Pinot Noir Wine, 12 oz"
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=1166),
                        "carbohydrates": Weight(g=64),
                        "calories": Energy(Calorie=690),
                        "fat": Weight(g=48),
                        "sugar": Weight(g=14),
                        "protein": Weight(g=30)
                    },
                    "name": "Generic - Baked Macaroni and Cheese, 14 grams"
                }
            ],
            "snacks": [
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=80),
                        "carbohydrates": Weight(g=3),
                        "calories": Energy(Calorie=170),
                        "fat": Weight(g=2),
                        "sugar": Weight(g=2),
                        "protein": Weight(g=36)
                    },
                    "name": "Mrm - Dutch Chocolate Whey Protein, 2 scoop"
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=338),
                        "carbohydrates": Weight(g=36),
                        "calories": Energy(Calorie=203),
                        "fat": Weight(g=6),
                        "sugar": Weight(g=34),
                        "protein": Weight(g=2)
                    },
                    "name": "Drinks - Almond Milk (Vanilla), 18 oz"
                },
                {
                    "nutrition_information": {
                        "sodium": Weight(mg=0),
                        "carbohydrates": Weight(g=48),
                        "calories": Energy(Calorie=588),
                        "fat": Weight(g=0),
                        "sugar": Weight(g=0),
                        "protein": Weight(g=0)
                    },
                    "name": (
                        "Dogfish Head 90 Minute Ipa - "
                        "Beer, India Pale Ale, 24 oz"
                    )
                }
            ]
        }
        actual_dict = day.get_as_dict()

        self.assertEquals(
            expected_dict,
            actual_dict,
        )
        self.assertEquals(
            day.date,
            self.arbitrary_date,
        )
        self.assertEquals(
            day.goals,
            {
                'calories': Energy(Calorie=2500),
                'carbohydrates': Weight(g=343),
                'fat': Weight(g=84),
                'protein': Weight(g=93),
                'sodium': Weight(mg=2500),
                'sugar': Weight(g=50),
            }
        )
        self.assertEquals(
            day.totals,
            {
                'calories': Energy(Calorie=2279),
                'carbohydrates': Weight(g=203),
                'fat': Weight(g=73),
                'protein': Weight(g=78),
                'sodium': Weight(mg=2069),
                'sugar': Weight(g=58),
            }
        )
