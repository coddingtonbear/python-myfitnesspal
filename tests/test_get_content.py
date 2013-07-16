import datetime

import mimic

from myfitnesspal import Client

from .base import MFPTestCase

class TestGetContent(MFPTestCase):
    def setUp(self):
        self.arbitrary_username = 'alpha'
        self.arbitrary_password = 'beta'
        self.arbitrary_date = datetime.date(2013,3,2)
        self.client = Client(
            self.arbitrary_username,
            self.arbitrary_password,
        )
        super(TestGetContent, self).setUp()

    def _stub_response_document(self, filename):
        self.mimic.stub_out_with_mock(
            self.client,
            '_get_content_for_url'
        )
        self.client._get_content_for_url(
            mimic.IgnoreArg()
        ).and_return(
            self.get_html_document(
                filename
            )
        )

    def test_get_day(self):
        self._stub_response_document('2013-07-13.html')

        self.mimic.replay_all()

        day = self.client.get_date(self.arbitrary_date)

        self.assertEquals(
            day.date,
            self.arbitrary_date,
        )
        self.assertEquals(
            len(list(day.entries)),
            5
        )
        self.assertEquals(
            len(day.meals),
            4
        )
        self.assertEquals(
            day.totals,
            {
                'calories': 2342,
                'carbohydrates': 269,
                'fat': 90,
                'protein': 134,
                'sodium': 3535,
                'sugar': 42,
            }
        )
        self.assertEquals(
            day.goals,
            {
                'calories': 2500,
                'carbohydrates': 343,
                'fat': 84,
                'protein': 93,
                'sodium': 2500,
                'sugar': 50,
            }
        )
