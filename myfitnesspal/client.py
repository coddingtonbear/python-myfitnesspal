from __future__ import annotations

import datetime
import json
import logging
import re
import uuid
from collections import OrderedDict
from http.cookiejar import CookieJar
from pathlib import Path
from typing import Any, Dict, List, Optional, Union, cast, overload
from urllib import parse

import browser_cookie3
import cloudscraper
import lxml.html
import requests
from measurement.base import MeasureBase
from measurement.measures import Energy, Mass, Volume

from . import types
from .base import MFPBase
from .day import Day
from .entry import Entry
from .exceptions import MyfitnesspalLoginError, MyfitnesspalRequestFailed
from .exercise import Exercise
from .fooditem import FoodItem
from .meal import Meal
from .note import Note

logger = logging.getLogger(__name__)

BRITISH_UNIT_MATCHER = re.compile(r"(?:(?P<st>\d+) st)\W*(?:(?P<lbs>\d+) lb)?")


class Client(MFPBase):
    """Provides access to MyFitnessPal APIs"""

    COOKIE_DOMAINS = [
        "myfitnesspal.com",
        "www.myfitnesspal.com",
    ]
    BASE_URL = "http://www.myfitnesspal.com/"
    BASE_URL_SECURE = "https://www.myfitnesspal.com/"
    BASE_API_URL = "https://api.myfitnesspal.com/"
    LOGIN_FORM_PATH = "account/login"
    LOGIN_JSON_PATH = "api/auth/callback/credentials"
    CSRF_PATH = "api/auth/csrf"
    SEARCH_PATH = "food/search"
    ABBREVIATIONS = {
        "carbs": "carbohydrates",
    }
    DEFAULT_MEASURE_AND_UNIT = {
        "calories": (Energy, "Calorie"),
        "carbohydrates": (Mass, "g"),
        "fat": (Mass, "g"),
        "protein": (Mass, "g"),
        "sodium": (Mass, "mg"),
        "sugar": (Mass, "g"),
        "fiber": (Mass, "g"),
        "potass.": (Mass, "mg"),
        "kilojoules": (Energy, "kJ"),
    }

    def __init__(
        self,
        cookiejar: Optional[CookieJar] = None,
        unit_aware: bool = False,
        log_requests_to: Path | None = None,
    ):
        self._client_instance_id = uuid.uuid4()
        self._request_counter = 0
        self._log_requests_to: Path | None = None
        if log_requests_to:
            self._log_requests_to = log_requests_to / Path(
                str(self._client_instance_id)
            )
            self._log_requests_to.mkdir(parents=True, exist_ok=True)

        self.unit_aware = unit_aware

        self.session = cloudscraper.create_scraper(sess=requests.Session())
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
            }
        )
        if cookiejar is not None:
            self.session.cookies.update(cookiejar)
        else:
            for domain_name in self.COOKIE_DOMAINS:
                self.session.cookies.update(
                    browser_cookie3.load(domain_name=domain_name)
                )

        self._auth_data = self._get_auth_data()
        self._user_metadata = self._get_user_metadata()

    @property
    def user_id(self) -> Optional[types.MyfitnesspalUserId]:
        """The user_id of the logged-in account."""
        if self._auth_data is None:
            return None

        return self._auth_data["user_id"]

    @property
    def user_metadata(self) -> types.UserMetadata:
        """Metadata about of the logged-in account."""
        return self._user_metadata

    @property
    def access_token(self) -> Optional[str]:
        """The access token for the logged-in account."""
        if self._auth_data is None:
            return None

        return self._auth_data["access_token"]

    @property
    def effective_username(self) -> str:
        """One's actual username may be different from the one used for login

        This method will return the actual username if it is available, but
        will fall back to the one provided if it is not.

        """
        return self.user_metadata["username"]

    def _get_auth_data(self) -> types.AuthData:
        result = self._get_request_for_url(
            parse.urljoin(self.BASE_URL_SECURE, "/user/auth_token") + "?refresh=true"
        )
        if not result.ok:
            raise MyfitnesspalRequestFailed(
                "Unable to fetch authentication token from MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )

        if not result.headers["Content-Type"].startswith("application/json"):
            # That we didn't receive a JSON document for this request
            # is the only obvious clear signal that we aren't logged-in.
            raise MyfitnesspalLoginError(
                "Could not access MyFitnessPal using the cookies provided "
                "by your browser.  Are you sure you have logged in to "
                "MyFitnessPal using a browser on this computer?"
            )

        return result.json()

    def _get_user_metadata(self) -> types.UserMetadata:
        requested_fields = [
            "diary_preferences",
            "goal_preferences",
            "unit_preferences",
            "paid_subscriptions",
            "account",
            "goal_displays",
            "location_preferences",
            "system_data",
            "profiles",
            "step_sources",
            "privacy_preferences",
            "social_preferences",
            "app_preferences",
            "partner_only_fields",
        ]
        query_string = parse.urlencode(
            [
                (
                    "fields[]",
                    name,
                )
                for name in requested_fields
            ]
        )
        metadata_url = (
            parse.urljoin(self.BASE_API_URL, f"/v2/users/{self.user_id}")
            + "?"
            + query_string
        )
        result = self._get_request_for_url(metadata_url, send_token=True)
        if not result.ok:
            logger.warning(
                "Unable to fetch user metadata; this may cause Myfitnesspal "
                "to behave incorrectly if you have logged-in with your "
                "e-mail address rather than your basic username; status %s.",
                result.status_code,
            )

        return result.json()["item"]

    def _get_full_name(self, raw_name: str) -> str:
        name = raw_name.lower().strip()
        if name not in self.ABBREVIATIONS:
            return name
        return self.ABBREVIATIONS[name]

    def _get_url_for_date(
        self, date: datetime.date, username: str, friend_username=None
    ) -> str:
        if friend_username is not None:
            name = friend_username
        else:
            name = username
        date_str = date.strftime("%Y-%m-%d")
        return (
            parse.urljoin(self.BASE_URL_SECURE, "food/diary/" + name)
            + f"?date={date_str}"
        )

    def _get_url_for_measurements(
        self, page: int = 1, measurement_name: str = ""
    ) -> str:
        return (
            parse.urljoin(self.BASE_URL_SECURE, "measurements/edit")
            + "?"
            + parse.urlencode({"page": page, "type": measurement_name})
        )

    def _get_request_for_url(
        self,
        url: str,
        send_token: bool = False,
        headers: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> requests.Response:
        request_id = uuid.uuid4()
        self._request_counter += 1
        logger.debug(
            "Sending request %s (#%s for client) to url %s",
            self._request_counter,
            request_id,
            url,
        )
        if headers is None:
            headers = {}

        if send_token:
            headers.update(
                {
                    "Authorization": f"Bearer {self.access_token}",
                    "mfp-client-id": "mfp-main-js",
                }
            )
            if self.user_id:
                headers["mfp-user-id"] = self.user_id

        result = self.session.get(url, headers=headers, **kwargs)
        if self._log_requests_to:
            with open(
                self._log_requests_to
                / Path(
                    str(self._request_counter).zfill(3) + "__" + str(request_id)
                ).with_suffix(".json"),
                "w",
                encoding="utf-8",
            ) as outf:
                outf.write(
                    json.dumps(
                        {
                            "request": {
                                "url": url,
                                "send_token": send_token,
                                "user_id": self.user_id if send_token else None,
                                "headers": headers,
                                "kwargs": kwargs,
                            },
                            "response": {
                                "headers": dict(result.headers),
                                "status_code": result.status_code,
                                "content": result.content.decode("utf-8"),
                            },
                        },
                        indent=4,
                        sort_keys=True,
                    )
                )

        return result

    def _get_content_for_url(self, *args, **kwargs) -> str:
        return self._get_request_for_url(*args, **kwargs).content.decode("utf8")

    def _get_document_for_url(self, url):
        content = self._get_content_for_url(url)

        return lxml.html.document_fromstring(content)

    def _get_json_for_url(self, url):
        content = self._get_content_for_url(url)

        return json.loads(content)

    def _get_measurement(self, name: str, value: Optional[float]) -> MeasureBase:
        if not self.unit_aware:
            return value
        measure, kwarg = self.DEFAULT_MEASURE_AND_UNIT[name]
        return measure(**{kwarg: value})

    def _get_numeric(self, string: str) -> float:
        matched = BRITISH_UNIT_MATCHER.match(string)
        if matched:
            return float(matched.groupdict()["lbs"] or 0) + (
                float(matched.groupdict()["st"] or 0) * 14
            )
        else:
            try:
                str_value = re.sub(r"[^-\d.]+", "", string)
                return float(str_value)
            except ValueError:
                return 0

    def _get_fields(self, document):
        meal_header = document.xpath("//tr[@class='meal_header']")[0]
        tds = meal_header.findall("td")
        fields = ["name"]
        for field in tds[1:]:
            fields.append(self._get_full_name(field.text))
        return fields

    def _get_goals(self, document):
        try:
            total_header = document.xpath("//tr[@class='total']")[0]
        except IndexError:
            return None

        goal_header = total_header.getnext()  # The following TR contains goals
        columns = goal_header.findall("td")

        fields = self._get_fields(document)

        nutrition = {}
        for n in range(1, len(columns)):
            column = columns[n]
            try:
                nutr_name = fields[n]
            except IndexError:
                # This is the 'delete' button
                continue
            value = self._extract_value(column)
            nutrition[nutr_name] = self._get_measurement(nutr_name, value)

        return nutrition

    def _get_completion(self, document) -> bool:
        try:
            completion_header = document.xpath("//div[@id='complete_day']")[0]
            completion_message = completion_header.getchildren()[0]

            if "day_incomplete_message" in completion_message.classes:
                return False
            elif "day_complete_message" in completion_message.classes:
                return True
        except IndexError:
            pass

        return False  # Who knows, probably not my diary.

    def _get_meals(self, document) -> List[Meal]:
        meals = []
        fields = None
        meal_headers = document.xpath("//tr[@class='meal_header']")

        for meal_header in meal_headers:
            tds = meal_header.findall("td")
            meal_name = tds[0].text.lower()
            if fields is None:
                fields = self._get_fields(document)
            this = meal_header
            entries = []

            while True:
                this = this.getnext()
                if not this.attrib.get("class") is None:
                    break
                columns = this.findall("td")

                # When viewing a friend's diary, the HTML entries containing the
                # actual food log entries are different: they don't contain an
                # embedded <a/> element but rather the food name directly.
                if columns[0].find("a") is None:
                    name = columns[0].text.strip()
                else:
                    name = columns[0].find("a").text

                nutrition = {}

                for n in range(1, len(columns)):
                    column = columns[n]
                    try:
                        nutr_name = fields[n]
                    except IndexError:
                        # This is the 'delete' button
                        continue

                    value = self._extract_value(column)

                    nutrition[nutr_name] = self._get_measurement(nutr_name, value)

                entries.append(
                    Entry(
                        name,
                        nutrition,
                    )
                )

            meals.append(
                Meal(
                    meal_name,
                    entries,
                )
            )

        return meals

    def _get_url_for_exercise(self, date: datetime.date, username: str) -> str:
        date_str = date.strftime("%Y-%m-%d")
        return (
            parse.urljoin(self.BASE_URL_SECURE, "exercise/diary/" + username)
            + f"?date={date_str}"
        )

    def _get_exercise(self, document):
        exercises = []
        ex_headers = document.xpath("//table[@class='table0']")

        for ex_header in ex_headers:
            fields = []
            tds = ex_header.findall("thead")[0].findall("tr")[0].findall("td")
            ex_name = tds[0].text.lower()
            if len(fields) == 0:
                for field in tds:
                    fields.append(self._get_full_name(field.text))
            row = ex_header.findall("tbody")[0].findall("tr")[0]
            entries = []
            while True:
                if not row.attrib.get("class") is None:
                    break
                columns = row.findall("td")

                # Cardio diary exercise descriptions are anchor tags
                # within divs, but strength training exercise
                # descriptions are just anchor tags within the td.

                # But *first* we need to check whether an anchor
                # tag exists, or we throw an error looking for
                # an anchor tag within a div that doesn't exist

                # check for `td > a`
                name = ""
                if columns[0].find("a") is not None:
                    name = columns[0].find("a").text.strip()

                # If name is empty string:
                if columns[0].find("a") is None or not name:
                    # check for `td > div > a`
                    if columns[0].find("div").find("a") is None:
                        # then check for just `td > div`
                        # (this will occur when viewing a public diary entry)
                        if columns[0].find("div") is not None:
                            # if it exists, return `td > div.text`
                            name = columns[0].find("div").text.strip()
                        else:
                            # if neither, return `td.text`
                            name = columns[0].text.strip()
                    else:
                        # otherwise return `td > div > a.text`
                        name = columns[0].find("div").find("a").text.strip()

                attrs = {}

                for n in range(1, len(columns)):
                    column = columns[n]
                    try:
                        attr_name = fields[n]
                    except IndexError:
                        # This is the 'delete' button
                        continue

                    if column.text is None or "N/A" in column.text:
                        value = None
                    else:
                        value = self._get_numeric(column.text)

                    attrs[attr_name] = self._get_measurement(attr_name, value)

                entries.append(Entry(name, attrs))
                row = row.getnext()

            exercises.append(Exercise(ex_name, entries))

        return exercises

    def _get_exercises(self, date: datetime.date, friend_username=None):
        if friend_username is not None:
            name = friend_username
        else:
            name = self.effective_username
        # get the exercise URL
        document = self._get_document_for_url(self._get_url_for_exercise(date, name))
        # gather the exercise goals
        exercise = self._get_exercise(document)
        return exercise

    def _extract_value(self, element):
        if len(element.getchildren()) == 0:
            value = self._get_numeric(element.text)
        else:
            value = self._get_numeric(
                element.xpath("span[@class='macro-value']")[0].text
            )

        return value

    @overload
    def get_date(self, year: int, month: int, day: int) -> Day:
        ...

    @overload
    def get_date(self, date: datetime.date) -> Day:
        ...

    def get_date(self, *args, **kwargs) -> Day:
        """Returns your meal diary for a particular date"""
        if len(args) == 3:
            date = datetime.date(
                int(args[0]),
                int(args[1]),
                int(args[2]),
            )
        elif len(args) == 1 and isinstance(args[0], datetime.date):
            date = args[0]
        else:
            raise ValueError(
                "get_date accepts either a single datetime or date instance, "
                "or three integers representing year, month, and day "
                "respectively."
            )
        friend_username = kwargs.get("friend_username")
        document = self._get_document_for_url(
            self._get_url_for_date(
                date,
                kwargs.get("username", self.effective_username),
                friend_username,
            )
        )
        if "diary is locked with a key" in document.text_content():
            raise Exception("Error: diary is locked with a key")
        if (
            friend_username is not None
            and "user maintains a private diary" in document.text_content()
        ):
            raise Exception(
                f"Error: Friend {kwargs.get('friend_username')}'s diary is private."
            )

        meals = self._get_meals(document)
        goals = self._get_goals(document)
        complete = self._get_completion(document)

        # Since this data requires an additional request, let's just
        # allow the day object to run the request if necessary.
        notes = lambda: self._get_notes(date)  # noqa: E731
        water = lambda: self._get_water(date)  # noqa: E731
        exercises = lambda: self._get_exercises(date, friend_username)  # noqa: E731

        if "friend_username" not in kwargs:
            day = Day(
                date=date,
                meals=meals,
                goals=goals,
                notes=notes,
                water=water,
                exercises=exercises,
                complete=complete,
            )
        else:
            day = Day(
                date=date,
                meals=meals,
                goals=goals,
                exercises=exercises,
                complete=complete,
            )
        return day

    def _ensure_upper_lower_bound(self, lower_bound, upper_bound):
        if upper_bound is None:
            upper_bound = datetime.date.today()
        if lower_bound is None:
            lower_bound = upper_bound - datetime.timedelta(days=30)

        # If they entered the dates in the opposite order, let's
        # just flip them around for them as a convenience
        if lower_bound > upper_bound:
            lower_bound, upper_bound = upper_bound, lower_bound
        return upper_bound, lower_bound

    def get_measurements(
        self,
        measurement="Weight",
        lower_bound: Optional[datetime.date] = None,
        upper_bound: Optional[datetime.date] = None,
    ) -> Dict[datetime.date, float]:
        """Returns measurements of a given name between two dates."""
        upper_bound, lower_bound = self._ensure_upper_lower_bound(
            lower_bound, upper_bound
        )

        # get the URL for the main check in page
        document = self._get_document_for_url(self._get_url_for_measurements())

        # gather the IDs for all measurement types
        measurement_ids = self._get_measurement_ids(document)

        if measurement not in measurement_ids.keys():
            raise ValueError(f"Measurement '{measurement}' does not exist.")

        page = 1
        measurements = OrderedDict()

        # retrieve entries until finished
        while True:
            # retrieve the HTML from MyFitnessPal
            document = self._get_document_for_url(
                self._get_url_for_measurements(page, measurement)
            )

            # parse the HTML for measurement entries and add to dictionary
            results = self._get_measurements(document)
            measurements.update(results)

            # stop if there are no more entries
            if len(results) == 0:
                break

            # continue if the lower bound has not been reached
            elif list(results.keys())[-1] > lower_bound:
                page += 1
                continue

            # otherwise stop
            else:
                break

        # remove entries that are not within the dates specified
        for date in list(measurements.keys()):
            if not upper_bound >= date >= lower_bound:
                del measurements[date]

        return measurements

    def set_measurements(
        self,
        measurement="Weight",
        value: Optional[float] = None,
        date: Optional[datetime.date] = None,
    ) -> None:
        """Sets measurement for today's date."""
        if value is None:
            raise ValueError("Cannot update blank value.")
        if date is None:
            date = datetime.datetime.now().date()
        if not isinstance(date, datetime.date):
            raise ValueError("Date must be a datetime.date object.")

        # get the URL for the main check in page
        # this is left in because we need to parse
        # the 'measurement' name to set the value.
        document = self._get_document_for_url(self._get_url_for_measurements())

        # get authenticity token for this particular form.
        authenticity_token = document.xpath(
            "//form[@action='/measurements/new']/input[@name='authenticity_token']/@value"
        )[0]

        # gather the IDs for all measurement types
        measurement_ids = self._get_measurement_ids(document)

        # get the authenticity token for this edit
        authenticity_token = document.xpath(
            "(//form[@action='/measurements/new']/input[@name='authenticity_token']/@value)",
            smart_strings=False,
        )[0]

        # check if the measurement exists before going too far
        if measurement not in measurement_ids.keys():
            raise ValueError(f"Measurement '{measurement}' does not exist.")

        # build the update url.
        update_url = parse.urljoin(self.BASE_URL_SECURE, "measurements/new")

        # setup a dict for the post
        data = {
            "authenticity_token": authenticity_token,
            "measurement[display_value]": value,
            "type": measurement_ids.get(measurement),
            "measurement[entry_date(2i)]": date.month,
            "measurement[entry_date(3i)]": date.day,
            "measurement[entry_date(1i)]": date.year,
        }

        # now post it.
        result = self.session.post(update_url, data=data)

        # throw an error if it failed.
        if not result.ok:
            raise MyfitnesspalRequestFailed(
                "Unable to update measurement in MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )

    def _get_measurements(self, document):
        measurements = []

        for next_data in document.xpath("//script[@id='__NEXT_DATA__']"):
            next_data_json = json.loads(next_data.text)
            for q in next_data_json["props"]["pageProps"]["dehydratedState"]["queries"]:
                if "measurements" in q["queryKey"]:
                    if "items" in q["state"]["data"]:
                        measurements += q["state"]["data"]["items"]

        measurements_dict = OrderedDict()

        # converts the date to a datetime object and the value to a float
        for entry in measurements:
            date = datetime.datetime.strptime(entry["date"], "%Y-%m-%d").date()
            if "unit" in entry:
                value = f"{entry['value']} {entry['unit']}"
            else:
                value = f"{entry['value']}"
            measurements_dict[date] = self._get_numeric(value)

        return measurements_dict

    def _get_measurement_ids(self, document) -> Dict[str, int]:
        ids = {}
        for next_data in document.xpath("//script[@id='__NEXT_DATA__']"):
            next_data_json = json.loads(next_data.text)
            for q in next_data_json["props"]["pageProps"]["dehydratedState"]["queries"]:
                if "measurementTypes" in q["queryKey"]:
                    for m in q["state"]["data"]:
                        ids[m["description"]] = m["id"]
                if "measurements" in q["queryKey"]:
                    if q["queryKey"][1] not in ids:
                        ids[q["queryKey"][1]] = ""

        return ids

    def _get_notes(self, date: datetime.date) -> Note:
        result = self._get_request_for_url(
            parse.urljoin(
                self.BASE_URL_SECURE,
                "/food/note",
            )
            + "?date={date}".format(date=date.strftime("%Y-%m-%d"))
        )
        return Note(result.json()["item"])

    def _get_water(self, date: datetime.date) -> Union[float, Volume]:
        result = self._get_request_for_url(
            parse.urljoin(
                self.BASE_URL_SECURE,
                "/food/water",
            )
            + "?date={date}".format(date=date.strftime("%Y-%m-%d"))
        )
        value = result.json()["item"]["milliliters"]
        if self.unit_aware:
            return Volume(ml=value)

        return value

    def get_report(
        self,
        report_name: str = "Net Calories",
        report_category: str = "Nutrition",
        lower_bound: Optional[datetime.date] = None,
        upper_bound: Optional[datetime.date] = None,
    ) -> Dict[datetime.date, float]:
        """
        Returns report data of a given name and category between two dates.
        """
        if lower_bound and ((datetime.date.today() - lower_bound).days > 80):
            logger.warning(
                "Report API may not be able to look back this far. Some results may be incorrect."
            )

        upper_bound, lower_bound = self._ensure_upper_lower_bound(
            lower_bound, upper_bound
        )

        assert upper_bound
        assert lower_bound

        # Get the URL for the report
        json_data = self._get_json_for_url(
            self._get_url_for_report(report_name, report_category, lower_bound)
        )

        report = OrderedDict(self._get_report_data(json_data))

        if not report:
            raise ValueError("Could not load any results for the given category & name")

        # Remove entries that are not within the dates specified
        for date in list(report.keys()):
            if not upper_bound >= date >= lower_bound:
                del report[date]

        return report

    def _get_url_for_report(
        self, report_name: str, report_category: str, lower_bound: datetime.date
    ) -> str:
        delta = datetime.date.today() - lower_bound
        return (
            parse.urljoin(
                self.BASE_URL_SECURE,
                "reports/results/" + report_category.lower() + "/" + report_name,
            )
            + f"/{str(delta.days)}.json"
        )

    def _get_report_data(self, json_data: dict) -> Dict[datetime.date, float]:
        report_data: Dict[datetime.date, float] = {}

        data = json_data.get("data")

        if not data:
            return report_data

        for index, entry in enumerate(data):
            # Dates are returned without year.
            # As the returned dates will always begin from the current day, the
            # correct date can be determined using the entry's index
            date = (
                datetime.date.today()
                - datetime.timedelta(days=len(data))
                + datetime.timedelta(days=index + 1)
            )

            report_data.update({date: entry["total"]})

        return report_data

    def __str__(self) -> str:
        return f"MyFitnessPal Client for {self.effective_username}"

    def get_food_search_results(self, query: str) -> List[FoodItem]:
        """Search for foods matching a specified query."""
        search_url = parse.urljoin(self.BASE_URL_SECURE, self.SEARCH_PATH)
        document = self._get_document_for_url(search_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]

        result = self.session.post(
            search_url,
            data={
                "authenticity_token": authenticity_token,
                "search": query,
                "date": datetime.datetime.today().strftime("%Y-%m-%d"),
                "meal": "0",
            },
        )

        # result.content is bytes so we decode it ASSUMING utf8 (which may be a
        # bad assumption?) PORTING_CHECK
        content = result.content.decode("utf8")
        document = lxml.html.document_fromstring(content)
        if "Matching Foods:" not in content:
            raise MyfitnesspalRequestFailed("Unable to load search results.")

        return self._get_food_search_results(document)

    def _get_food_search_results(self, document) -> List[FoodItem]:
        item_divs = document.xpath("//li[@class='matched-food']")

        items = []
        for item_div in item_divs:
            # get mfp info from search results
            a = item_div.xpath(".//div[@class='search-title-container']/a")[0]
            mfp_id = int(a.get("data-external-id"))
            mfp_name = a.text
            verif = (
                True
                if item_div.xpath(".//div[@class='verified verified-list-icon']")
                else False
            )
            calories = None
            brand = ""
            nutr_info_xpath = item_div.xpath(".//p[@class='search-nutritional-info']")
            if nutr_info_xpath:
                nutr_info = nutr_info_xpath[0].text.strip().split(",")
                if len(nutr_info) >= 3:
                    brand = " ".join(nutr_info[0:-2]).strip()
                calories = float(nutr_info[-1].replace("calories", "").strip())
            items.append(
                FoodItem(mfp_id, mfp_name, brand, verif, calories, client=self)
            )

        return items

    def _get_food_item_details(self, mfp_id: int) -> types.FoodItemDetailsResponse:
        # api call for food item's details
        requested_fields = [
            "nutritional_contents",
            "serving_sizes",
            "confirmations",
        ]
        query_string = parse.urlencode(
            [
                (
                    "fields[]",
                    name,
                )
                for name in requested_fields
            ]
        )
        metadata_url = (
            parse.urljoin(self.BASE_API_URL, f"/v2/foods/{mfp_id}") + "?" + query_string
        )
        result = self._get_request_for_url(metadata_url, send_token=True)
        if not result.ok:
            raise MyfitnesspalRequestFailed()

        resp = result.json()["item"]

        # identifying calories for default serving
        nutr_info = resp["nutritional_contents"]
        if "energy" in nutr_info:
            calories = nutr_info["energy"]["value"]
        else:
            calories = 0.0

        return {
            "description": resp["description"],
            "brand_name": resp.get("brand_name"),
            "verified": resp["verified"],
            "nutrition": nutr_info,
            "calories": calories,
            "confirmations": resp["confirmations"],
            "serving_sizes": resp["serving_sizes"],
        }

    def get_food_item_details(self, mfp_id: int) -> FoodItem:
        """Get details about a specific food using its ID."""
        details = self._get_food_item_details(mfp_id)

        # returning food item's details
        return FoodItem(
            mfp_id,
            details["description"],
            details["brand_name"],
            details["verified"],
            details["calories"],
            details=details["nutrition"],
            confirmations=details["confirmations"],
            serving_sizes=details["serving_sizes"],
            client=self,
        )

    def set_new_food(
        self,
        brand: str,
        description: str,
        calories: int,
        fat: float,
        carbs: float,
        protein: float,
        sodium: Optional[float] = None,
        potassium: Optional[float] = None,
        saturated_fat: Optional[float] = None,
        polyunsaturated_fat: Optional[float] = None,
        fiber: Optional[float] = None,
        monounsaturated_fat: Optional[float] = None,
        sugar: Optional[float] = None,
        trans_fat: Optional[float] = None,
        cholesterol: Optional[float] = None,
        vitamin_a: Optional[float] = None,
        calcium: Optional[float] = None,
        vitamin_c: Optional[float] = None,
        iron: Optional[float] = None,
        serving_size: str = "1 Serving",
        servingspercontainer: float = 1.0,
        sharepublic: bool = False,
    ) -> None:
        """Function to submit new foods / groceries to the MyFitnessPal database. Function will return True if successful."""

        SUBMIT_PATH = "food/submit"
        SUBMIT_DUPLICATE_PATH = "food/duplicate"
        SUBMIT_NEW_PATH = (
            f"food/new?date={datetime.datetime.today().strftime('%Y-%m-%d')}&meal=0"
        )
        SUBMIT_POST_PATH = "food/new"

        # save current date in local variable for reusing
        date = datetime.datetime.today().strftime("%Y-%m-%d")

        # get Authenticity Token
        url = parse.urljoin(self.BASE_URL_SECURE, SUBMIT_PATH)
        document = self._get_document_for_url(url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath("(//input[@name='utf8']/@value)[1]")[0]

        # submit brand and description --> Possible returns duplicates warning
        url = parse.urljoin(self.BASE_URL_SECURE, SUBMIT_DUPLICATE_PATH)
        result = self.session.post(
            url,
            data={
                "utf8": utf8_field,
                "authenticity_token": authenticity_token,
                "date": date,
                "food[brand]": brand,
                "food[description]": description,
            },
        )
        if not result.ok:
            raise MyfitnesspalRequestFailed(
                f"Request Error - Unable to submit food to MyFitnessPal: status code: {result.status_code}"
            )

        # Check if a warning exists and log warning
        document = lxml.html.document_fromstring(result.content.decode("utf-8"))
        if document.xpath("//*[@id='main']/p[1]/span"):
            warning = document.xpath("//*[@id='main']/p[1]/span")[0].text
            logger.warning(f"My Fitness Pal responded: {warning}")
        # Passed Brand and Desc. Ready submit Form but needs new Authenticity Token
        url = parse.urljoin(self.BASE_URL_SECURE, SUBMIT_NEW_PATH)
        document = self._get_document_for_url(url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath("(//input[@name='utf8']/@value)[1]")[0]

        # Step4 - Build Post Data and finally submit new Food with nutritional Details
        data = {
            "utf8": utf8_field,
            "authenticity_token": authenticity_token,
            "date": date,
            "food[brand]": brand,
            "food[description]": description,
            "weight[serving_size]": serving_size,
            "servingspercontainer": f"{servingspercontainer}",
            "nutritional_content[calories]": f"{calories}",
            "nutritional_content[sodium]": f"{sodium or ''}",
            "nutritional_content[fat]": f"{fat}",
            "nutritional_content[potassium]": f"{potassium if potassium is not None else ''}",
            "nutritional_content[saturated_fat]": f"{saturated_fat if saturated_fat is not None else ''}",
            "nutritional_content[carbs]": f"{carbs}",
            "nutritional_content[polyunsaturated_fat]": f"{polyunsaturated_fat if polyunsaturated_fat is not None else ''}",
            "nutritional_content[fiber]": f"{fiber if fiber is not None else ''}",
            "nutritional_content[monounsaturated_fat]": f"{monounsaturated_fat if monounsaturated_fat is not None else ''}",
            "nutritional_content[sugar]": f"{sugar if sugar is not None else ''}",
            "nutritional_content[trans_fat]": f"{trans_fat if trans_fat is not None else ''}",
            "nutritional_content[protein]": f"{protein}",
            "nutritional_content[cholesterol]": f"{cholesterol if cholesterol is not None else ''}",
            "nutritional_content[vitamin_a]": f"{vitamin_a if vitamin_a is not None else ''}",
            "nutritional_content[calcium]": f"{calcium if calcium is not None else ''}",
            "nutritional_content[vitamin_c]": f"{vitamin_c if vitamin_c is not None else ''}",
            "nutritional_content[iron]": f"{iron if iron is not None else ''}",
            "food_entry[quantity]": "1.0",
            "food_entry[meal_id]": "0",
            "addtodiary": "no",
            "preserve_exact_description_and_brand": "true",
            "continue": "Save",
        }
        # Make entry public if requested, Hint: submit "sharefood": 0 also generates a public db entry, so only add
        # "sharefood"" if really requested
        if sharepublic:
            data["sharefood"] = 1

        url = parse.urljoin(self.BASE_URL_SECURE, SUBMIT_POST_PATH)
        result = self.session.post(
            url,
            data,
        )
        if not result.ok:
            raise MyfitnesspalRequestFailed(
                f"Request Error - Unable to submit food to MyFitnessPal: status code: {result.status_code}"
            )

        document = lxml.html.document_fromstring(result.content.decode("utf-8"))

        if document.xpath(
            # If list is empty there should be no error, could be replaced with assert
            "//*[@id='errorExplanation']/ul/li"
        ):
            error = document.xpath("//*[@id='errorExplanation']/ul/li")[0].text
            error = error.replace("Description ", "")  # For cosmetic reasons
            raise MyfitnesspalRequestFailed(
                f"Unable to submit food to MyFitnessPal: {error}"
            )

        # Would like to return FoodItem, but seems that it take
        # to long until the submitted food is available in the DB
        # return self.get_food_search_results("{} {}".format(brand, description))[0]

    def set_new_goal(
        self,
        energy: float,
        energy_unit: str = "calories",
        carbohydrates: Optional[float] = None,
        protein: Optional[float] = None,
        fat: Optional[float] = None,
        percent_carbohydrates: Optional[float] = None,
        percent_protein: Optional[float] = None,
        percent_fat: Optional[float] = None,
    ) -> None:
        """Updates your nutrition goals.

        This Function will update your nutrition goals and is able to deal with multiple situations based on the passed arguments.
        First matching situation will be applied and used to update the nutrition goals.

        Passed arguments - Hints:
        energy and all absolute macro values - Energy value will be adjusted/calculated if energy from macro values is higher than provided energy value.
        energy and all percentage macro values - Energy will be adjusted and split into macros by provided percentage.
        energy - Energy will be adjusted and split into macros by percentage as before.

        Optional arguments:
        energy_unit - Function is able to deal with calories and kilojoules. If not provided user preferences will be used.

        Additional hints:
        Values will be adjusted and rounded by MFP if no premium subscription is applied!
        """
        # FROM MFP JS:
        # var calculated_energy = 4 * parseFloat(this.get('carbGrams')) + 4 * parseFloat(this.get('proteinGrams')) + 9 * parseFloat(this.get('fatsGrams'));

        # Get User Default Unit Preference
        if energy_unit != "calories" and energy_unit != "kilojoules":
            assert self.user_metadata
            energy_unit = self.user_metadata["unit_preferences"]["energy"]

        # Get authenticity token and current values
        url = parse.urljoin(self.BASE_URL_SECURE, "account/my_goals")
        today = datetime.datetime.now().strftime("%Y-%m-%d")

        # Build header for API-requests
        auth_header = self.session.headers
        auth_header["authorization"] = f"Bearer {self.access_token}"
        auth_header["mfp-client-id"] = "mfp-main-js"
        auth_header["mfp-user-id"] = f"{self.user_id}"

        # Get Request for old goal values
        old_goals_url = parse.urljoin(
            self.BASE_API_URL, f"v2/nutrient-goals?date={today}"
        )
        old_goals_document = self.session.get(old_goals_url, headers=auth_header)
        old_goals = json.loads(old_goals_document.text)

        # Marcro Calculation
        # If no macro goals were provided calculate them with percentage value
        if carbohydrates is None or protein is None or fat is None:
            # If even no macro percentages values were provided calculate them from old values
            if (
                percent_carbohydrates is None
                or percent_protein is None
                or percent_fat is None
            ):
                old_energy_value = old_goals["items"][0]["default_goal"]["energy"][
                    "value"
                ]
                old_energy_unit = old_goals["items"][0]["default_goal"]["energy"][
                    "unit"
                ]
                old_carbohydrates = old_goals["items"][0]["default_goal"][
                    "carbohydrates"
                ]
                old_fat = old_goals["items"][0]["default_goal"]["fat"]
                old_protein = old_goals["items"][0]["default_goal"]["protein"]

                # If old and new values are in diffrent units then convert old value to new unit
                if not old_energy_unit == energy_unit:
                    if old_energy_unit not in ["kilojoules", "calories"]:
                        raise Exception(
                            f"Unexpected energy unit in historical goals: {old_energy_unit}"
                        )
                    if energy_unit not in ["kilojoules", "calories"]:
                        raise ValueError(
                            f"Unexpected energy unit in goals: {energy_unit}"
                        )

                    if old_energy_unit == "kilojoules" and energy_unit == "calories":
                        old_energy_value *= 0.2388
                        old_energy_unit = "calories"
                    elif old_energy_unit == "calories" and energy_unit == "kilojoules":
                        """FROM MFP JS
                        if (energyUnit === 'kilojoules') {
                            calories *= 4.184;
                        }
                        """
                        old_energy_value *= 4.184
                        old_energy_unit = "kilojoules"

                carbohydrates = energy * old_carbohydrates / old_energy_value
                protein = energy * old_protein / old_energy_value
                fat = energy * old_fat / old_energy_value
            # If percentage values were provided check
            else:
                if int(percent_carbohydrates + percent_protein + percent_fat) != 100:
                    raise ValueError("Provided percentage values do not add to 100%.")

                carbohydrates = energy * percent_carbohydrates / 100.0 / 4
                protein = energy * percent_protein / 100.0 / 4
                fat = energy * percent_fat / 100.0 / 9
                if energy_unit == "kilojoules":
                    carbohydrates = round(carbohydrates / 4.184, 2)
                    protein = round(protein / 4.184, 2)
                    fat = round(fat / 4.184, 2)
        else:
            macro_energy = carbohydrates * 4 + protein * 4 + fat * 9
            if energy_unit == "kilojoules":
                macro_energy *= 4.184
            # Compare energy values and set it correctly due to macros. Will also fix if no energy_value was provided.
            if energy < macro_energy:
                logger.warning(
                    "Provided energy value and calculated energy value from macros do not match! Will override!"
                )
                energy = macro_energy

        # Build payload based on observed browser behaviour
        new_goals = {}
        new_goals["item"] = old_goals["items"][0]
        new_goals["item"].pop("valid_to", None)
        new_goals["item"].pop("default_group_id", None)
        new_goals["item"].pop("updated_at", None)
        new_goals["item"]["default_goal"]["meal_goals"] = []

        # insert new values
        new_goals["item"]["valid_from"] = today

        new_goals["item"]["default_goal"]["energy"]["value"] = energy
        new_goals["item"]["default_goal"]["energy"]["unit"] = energy_unit
        new_goals["item"]["default_goal"]["carbohydrates"] = carbohydrates
        new_goals["item"]["default_goal"]["protein"] = protein
        new_goals["item"]["default_goal"]["fat"] = fat

        for goal in new_goals["item"]["daily_goals"]:
            goal["meal_goals"] = []
            goal.pop("group_id", None)

            goal["energy"]["value"] = energy
            goal["energy"]["unit"] = energy_unit
            goal["carbohydrates"] = carbohydrates
            goal["protein"] = protein
            goal["fat"] = fat

        # Build request and post
        url = parse.urljoin(self.BASE_API_URL, "v2/nutrient-goals")
        result = self.session.post(url, json.dumps(new_goals), headers=auth_header)

        if not result.ok:
            raise MyfitnesspalRequestFailed(
                "Request Error - Unable to submit Goals to MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )

    def get_recipes(self) -> Dict[int, str]:
        """Returns a dictionary with all saved recipes.

        Recipe ID will be used as dictionary key, recipe title as dictionary value.
        """
        recipes_dict = {}

        page_count = 1
        has_next_page = True
        while has_next_page:
            RECIPES_PATH = f"recipe_parser?page={page_count}&sort_order=recent"
            recipes_url = parse.urljoin(self.BASE_URL_SECURE, RECIPES_PATH)
            document = self._get_document_for_url(recipes_url)
            recipes = document.xpath(
                "//*[@id='main']/ul[1]/li"
            )  # get all items in the recipe list
            for recipe_info in recipes:
                recipe_path = recipe_info.xpath("./div[2]/h2/span[1]/a")[0].attrib[
                    "href"
                ]
                recipe_id = recipe_path.split("/")[-1]
                recipe_title = recipe_info.xpath("./div[2]/h2/span[1]/a")[0].attrib[
                    "title"
                ]
                recipes_dict[recipe_id] = recipe_title

            # Check for Pagination
            pagination_links = document.xpath('//*[@id="main"]/ul[2]/a')
            if pagination_links:
                if page_count == 1:
                    # If Pagination exists and it is page 1 there have to be a second,
                    # but only one href to the next (obviously none to the previous)
                    page_count += 1
                elif len(pagination_links) > 1:
                    # If there are two links, ont to the previous and one to the next
                    page_count += 1
                else:
                    # Only one link means it is the last page
                    has_next_page = False
            else:
                # Indicator for no recipes if len(recipes_dict) is 0 here
                has_next_page = False

        return recipes_dict

    def get_recipe(self, recipeid: int) -> types.Recipe:
        """Returns recipe details in a dictionary.

        See https://schema.org/Recipe for details regarding this schema.
        """
        recipe_path = f"/recipe/view/{recipeid}"
        recipe_url = parse.urljoin(self.BASE_URL_SECURE, recipe_path)
        document = self._get_document_for_url(recipe_url)

        recipe_dict: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "author": self.effective_username,
        }
        recipe_dict["org_url"] = recipe_url
        recipe_dict["name"] = document.xpath('//*[@id="main"]/div[3]/div[2]/h1')[0].text
        recipe_dict["recipeYield"] = document.xpath('//*[@id="recipe_servings"]')[
            0
        ].text

        recipe_dict["recipeIngredient"] = []
        ingredients = document.xpath('//*[@id="main"]/div[4]/div/*/li')
        for ingredient in ingredients:
            recipe_dict["recipeIngredient"].append(ingredient.text.strip(" \n"))

        recipe_dict["nutrition"] = {"@type": "NutritionInformation"}
        recipe_dict["nutrition"]["calories"] = document.xpath(
            '//*[@id="main"]/div[3]/div[2]/div[2]/div'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["carbohydrateContent"] = document.xpath(
            '//*[@id="carbs"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["fiberContent"] = document.xpath(
            '//*[@id="fiber"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["sugarContent"] = document.xpath(
            '//*[@id="sugar"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["sodiumContent"] = document.xpath(
            '//*[@id="sodium"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["proteinContent"] = document.xpath(
            '//*[@id="protein"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["fatContent"] = document.xpath(
            '//*[@id="total_fat"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["saturatedFatContent"] = document.xpath(
            '//*[@id="saturated_fat"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["monounsaturatedFatContent"] = document.xpath(
            '//*[@id="monounsaturated_fat"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["polyunsaturatedFatContent"] = document.xpath(
            '//*[@id="polyunsaturated_fat"]/td[1]/span[2]'
        )[0].text.strip(" \n")
        recipe_dict["nutrition"]["unsaturatedFatContent"] = int(
            recipe_dict["nutrition"]["polyunsaturatedFatContent"]
        ) + int(recipe_dict["nutrition"]["monounsaturatedFatContent"])
        recipe_dict["nutrition"]["transFatContent"] = document.xpath(
            '//*[@id="trans_fat"]/td[1]/span[2]'
        )[0].text.strip(" \n")

        # add some required tags to match schema
        recipe_dict["recipeInstructions"] = ""
        recipe_dict["tags"] = ["MyFitnessPal"]
        return cast(types.Recipe, recipe_dict)

    def get_meals(self) -> Dict[int, str]:
        """Returns a dictionary with all saved meals.

        Key: Meal ID
        Value: Meal Name
        """
        meals_dict = {}
        meals_path = "meal/mine"
        meals_url = parse.urljoin(self.BASE_URL_SECURE, meals_path)
        document = self._get_document_for_url(meals_url)

        meals = document.xpath(
            "//*[@id='matching']/li"
        )  # get all items in the recipe list
        _idx: Optional[int] = None
        try:
            for _idx, meal in enumerate(meals):
                meal_path = meal.xpath("./a")[0].attrib["href"]
                meal_id = meal_path.split("/")[-1].split("?")[0]
                meal_title = meal.xpath("./a")[0].text
                meals_dict[meal_id] = meal_title
        except Exception:
            # no meals available?
            logger.warning(f"Could not extract meal at index {_idx}")

        return meals_dict

    def get_meal(self, meal_id: int, meal_title: str) -> types.Recipe:
        """Returns meal details.

        See https://schema.org/Recipe for details regarding this schema.
        """

        meal_path = f"/meal/update_meal_ingredients/{meal_id}"
        meal_url = parse.urljoin(self.BASE_URL_SECURE, meal_path)
        document = self._get_document_for_url(meal_url)

        recipe_dict: Dict[str, Any] = {
            "@context": "https://schema.org",
            "@type": "Recipe",
            "author": self.effective_username,
        }
        recipe_dict["org_url"] = meal_url
        recipe_dict["name"] = meal_title
        recipe_dict["recipeYield"] = 1
        recipe_dict["recipeIngredient"] = []
        ingredients = document.xpath('//*[@id="meal-table"]/tbody/tr')
        # No ingredients?
        if len(ingredients) == 1 and ingredients[0].xpath("./td[1]")[0].text == "\xa0":
            raise Exception("No ingredients found when fetching meal.")
        else:
            for ingredient in ingredients:
                recipe_dict["recipeIngredient"].append(
                    ingredient.xpath("./td[1]")[0].text
                )

            total = document.xpath('//*[@id="mealTableTotal"]/tbody/tr')[0]
            recipe_dict["nutrition"] = {"@type": "NutritionInformation"}
            recipe_dict["nutrition"]["calories"] = total.xpath("./td[2]")[0].text
            recipe_dict["nutrition"]["carbohydrateContent"] = total.xpath("./td[3]")[
                0
            ].text
            recipe_dict["nutrition"]["proteinContent"] = total.xpath("./td[5]")[0].text
            recipe_dict["nutrition"]["fatContent"] = total.xpath("./td[4]")[0].text
            recipe_dict["nutrition"]["sugarContent"] = total.xpath("./td[7]")[0].text
            recipe_dict["nutrition"]["sodiumContent"] = total.xpath("./td[6]")[0].text

        # add some required tags to match schema
        recipe_dict["recipeInstructions"] = ""
        recipe_dict["tags"] = ["MyFitnessPal"]
        return cast(types.Recipe, recipe_dict)
