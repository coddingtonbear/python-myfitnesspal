from __future__ import annotations

import datetime
import json
import logging
import re
from collections import OrderedDict
from typing import Dict, List, Optional, Union, overload

import lxml.html
import requests
from measurement.base import MeasureBase
from measurement.measures import Energy, Mass, Volume
from six.moves.urllib import parse

from . import types
from .base import MFPBase
from .day import Day
from .entry import Entry
from .exceptions import MyfitnesspalLoginError, MyfitnesspalRequestFailed
from .exercise import Exercise
from .fooditem import FoodItem
from .keyring_utils import get_password_from_keyring
from .meal import Meal
from .note import Note

logger = logging.getLogger(__name__)

BRITISH_UNIT_MATCHER = re.compile(r"(?:(?P<st>\d+) st)\W*(?:(?P<lbs>\d+) lb)?")


class Client(MFPBase):
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

    def __init__(self, username, password=None, login=True, unit_aware=False):
        self.provided_username = username
        if password is None:
            password = get_password_from_keyring(username)
        self.__password = password
        self.unit_aware = unit_aware

        self._user_metadata: Optional[types.UserMetadata] = None
        self._auth_data: Optional[types.AuthData] = None

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
            }
        )
        if login:
            self._login()

    @property
    def user_id(self) -> Optional[types.MyfitnesspalUserId]:
        if self._auth_data is None:
            return None

        return self._auth_data["user_id"]

    @property
    def user_metadata(self) -> Optional[types.UserMetadata]:
        return self._user_metadata

    @property
    def access_token(self) -> Optional[str]:
        if self._auth_data is None:
            return None

        return self._auth_data["access_token"]

    @property
    def effective_username(self) -> str:
        """One's actual username may be different from the one used for login

        This method will return the actual username if it is available, but
        will fall back to the one provided if it is not.

        """
        if self.user_metadata:
            return self.user_metadata["username"]
        return self.provided_username

    def _login(self):
        csrf_url = parse.urljoin(self.BASE_URL_SECURE, self.CSRF_PATH)
        csrf_token = self._get_json_for_url(csrf_url)["csrfToken"]

        login_json_url = parse.urljoin(self.BASE_URL_SECURE, self.LOGIN_JSON_PATH)

        result = self.session.post(
            login_json_url,
            data={
                "csrfToken": csrf_token,
                "username": self.effective_username,
                "password": self.__password,
                "redirect": False,
                "json": True,
            },
        )
        if "error=CredentialsSignin" in result.url:
            raise MyfitnesspalLoginError()

        self._auth_data = self._get_auth_data()
        self._user_metadata = self._get_user_metadata()

    def _get_auth_data(self) -> types.AuthData:
        result = self._get_request_for_url(
            parse.urljoin(self.BASE_URL_SECURE, "/user/auth_token") + "?refresh=true"
        )
        if not result.ok:
            raise MyfitnesspalRequestFailed(
                "Unable to fetch authentication token from MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
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

    def _get_url_for_date(self, date: datetime.date, username: str) -> str:
        date_str = date.strftime("%Y-%m-%d")
        return (
                parse.urljoin(self.BASE_URL_SECURE, "food/diary/" + username)
                + f"?date={date_str}"
        )

    def _get_url_for_measurements(self, page: int = 1, measurement_id: int = 1) -> str:
        return (
                parse.urljoin(self.BASE_URL_SECURE, "measurements/edit")
                + f"?page={page}&type={measurement_id}"
        )

    def _get_request_for_url(
            self,
            url: str,
            send_token: bool = False,
            headers: Optional[Dict[str, str]] = None,
            **kwargs,
    ) -> requests.Response:
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

        return self.session.get(url, headers=headers, **kwargs)

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
                str_value = re.sub(r"[^\d.]+", "", string)
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

    def _get_exercises(self, date: datetime.date):
        # get the exercise URL
        document = self._get_document_for_url(
            self._get_url_for_exercise(date, self.effective_username)
        )

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
        document = self._get_document_for_url(
            self._get_url_for_date(
                date, kwargs.get("username", self.effective_username)
            )
        )

        meals = self._get_meals(document)
        goals = self._get_goals(document)
        complete = self._get_completion(document)

        # Since this data requires an additional request, let's just
        # allow the day object to run the request if necessary.
        notes = lambda: self._get_notes(date)  # noqa: E731
        water = lambda: self._get_water(date)  # noqa: E731
        exercises = lambda: self._get_exercises(date)  # noqa: E731

        day = Day(
            date=date,
            meals=meals,
            goals=goals,
            notes=notes,
            water=water,
            exercises=exercises,
            complete=complete,
        )

        return day

    def get_measurements(
            self, measurement="Weight", lower_bound=None, upper_bound=None
    ) -> Dict[datetime.date, float]:
        """Returns measurements of a given name between two dates."""
        if upper_bound is None:
            upper_bound = datetime.date.today()
        if lower_bound is None:
            lower_bound = upper_bound - datetime.timedelta(days=30)

        # If they entered the dates in the opposite order, let's
        # just flip them around for them as a convenience
        if lower_bound > upper_bound:
            lower_bound, upper_bound = upper_bound, lower_bound

        # get the URL for the main check in page
        document = self._get_document_for_url(self._get_url_for_measurements())

        # gather the IDs for all measurement types
        measurement_ids = self._get_measurement_ids(document)

        # select the measurement ID based on the input
        if measurement in measurement_ids.keys():
            measurement_id = measurement_ids[measurement]
        else:
            raise ValueError(f"Measurement '{measurement}' does not exist.")

        page = 1
        measurements = OrderedDict()

        # retrieve entries until finished
        while True:
            # retrieve the HTML from MyFitnessPal
            document = self._get_document_for_url(
                self._get_url_for_measurements(page, measurement_id)
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
            value: float = None,
            date: Optional[datetime.date] = None,
    ):
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
        authenticity_token = \
            document.xpath("(//form[@action='/measurements/new']/input[@name='authenticity_token']/@value)",
                           smart_strings=False)[0]

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
        # find the tr element for each measurement entry on the page
        trs = document.xpath("//table[contains(@class,'check-in')]/tbody/tr")

        measurements = OrderedDict()

        # create a dictionary out of the date and value of each entry
        for entry in trs:

            # ensure there are measurement entries on the page
            if len(entry) == 1:
                return measurements
            else:
                measurements[entry[1].text] = entry[2].text

        temp_measurements = OrderedDict()

        # converts the date to a datetime object and the value to a float
        for date in measurements:
            temp_measurements[
                datetime.datetime.strptime(date, "%m/%d/%Y").date()
            ] = self._get_numeric(measurements[date])

        measurements = temp_measurements

        return measurements

    def _get_measurement_ids(self, document) -> Dict[str, int]:

        # find the option element for all of the measurement choices
        options = document.xpath("//select[@id='type']/option")

        ids = {}

        # create a dictionary out of the text and value of each choice
        for option in options:
            ids[option.text] = int(option.attrib.get("value"))

        return ids

    def get_measurement_id_options(self) -> Dict[str, int]:
        """Returns list of measurement choices."""
        # get the URL for the main check in page
        document = self._get_document_for_url(self._get_url_for_measurements())

        # gather the IDs for all measurement types
        measurement_ids = self._get_measurement_ids(document)
        return measurement_ids

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

    def __str__(self) -> str:
        return f"MyFitnessPal Client for {self.effective_username}"

    def get_food_search_results(self, query: str) -> List[FoodItem]:
        search_url = parse.urljoin(self.BASE_URL_SECURE, self.SEARCH_PATH)
        document = self._get_document_for_url(search_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath("(//input[@name='utf8']/@value)[1]")[0]

        result = self.session.post(
            search_url,
            data={
                "utf8": utf8_field,
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
            nutr_info = (
                item_div.xpath(".//p[@class='search-nutritional-info']")[0]
                    .text.strip()
                    .split(",")
            )
            brand = ""
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

    ### Dominic Schwarz (Dnic94) <dominic.schwarz@dnic42.de> - 25.08.2021 ###
    ### Added function to submit new foods to MFP.
    SUBMIT_PATH = "food/submit"
    SUBMIT_DUPLICATE_PATH = "food/duplicate"
    SUBMIT_NEW_PATH = "food/new?date={}&meal=0".format(datetime.datetime.today().strftime("%Y-%m-%d"))
    SUBMIT_POST_PATH = "food/new"

    def set_new_food(self, brand: str, description: str, calories: int, fat: float, carbs: float, protein: float,
                     sodium: float = "", potassium: float = "", saturated_fat: float = "",
                     polyunsaturated_fat: float = "",
                     fiber: float = "", monounsaturated_fat: float = "", sugar: float = "", trans_fat: float = "",
                     cholesterol: float = "", vitamin_a: float = "", calcium: float = "", vitamin_c: float = "",
                     iron: float = "",
                     serving_size: str = "1 Serving", servingspercontainer: float = 1.0, sharepublic: bool = False):
        """Function to submit new foods / groceries to the MyFitnessPal database. Function will return True if successful."""

        # Step 1 to get Authenticity Token
        submit1_url = parse.urljoin(self.BASE_URL_SECURE, self.SUBMIT_PATH)
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        document = self._get_document_for_url(submit1_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath("(//input[@name='utf8']/@value)[1]")[0]

        # Step to to submit brand and description --> Possible returns duplicates warning
        submit2_url = parse.urljoin(self.BASE_URL_SECURE, self.SUBMIT_DUPLICATE_PATH)
        result = self.session.post(
            submit2_url,
            data={
                "utf8": utf8_field,
                "authenticity_token": authenticity_token,
                "date": datetime.datetime.today().strftime("%Y-%m-%d"),
                "food[brand]": brand,
                "food[description]": description
            },
        )
        if result.status_code == 200:
            # Check if a warning exists and log warning
            document = lxml.html.document_fromstring(result.content.decode('utf-8'))
            if document.xpath("//*[@id='main']/p[1]/span"):
                warning = document.xpath("//*[@id='main']/p[1]/span")[0].text
                logger.warning("My Fitness Pal responded: {}".format(warning))
        elif not result.ok:
            logger.warning(
                "Request Error - Unable to submit food to MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )
            return None

        # Step 3 - Passed Brand and Desc. Ready submit Form but needs new Authenticity Token
        submit3_url = parse.urljoin(self.BASE_URL_SECURE, self.SUBMIT_NEW_PATH)
        document = self._get_document_for_url(submit3_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath("(//input[@name='utf8']/@value)[1]")[0]

        # Step4 - Build Post Data and finally submit new Food with nutritional Details
        data = {
            "utf8": utf8_field,
            "authenticity_token": authenticity_token,
            "date": datetime.datetime.today().strftime("%Y-%m-%d"),
            "food[brand]": brand,
            "food[description]": description,
            "weight[serving_size]": serving_size,
            "servingspercontainer": "{}".format(servingspercontainer),
            "nutritional_content[calories]": "{}".format(calories),
            "nutritional_content[sodium]": "{}".format(sodium),
            "nutritional_content[fat]": "{}".format(fat),
            "nutritional_content[potassium]": "{}".format(potassium),
            "nutritional_content[saturated_fat]": "{}".format(saturated_fat),
            "nutritional_content[carbs]": "{}".format(carbs),
            "nutritional_content[polyunsaturated_fat]": "{}".format(polyunsaturated_fat),
            "nutritional_content[fiber]": "{}".format(fiber),
            "nutritional_content[monounsaturated_fat]": "{}".format(monounsaturated_fat),
            "nutritional_content[sugar]": "{}".format(sugar),
            "nutritional_content[trans_fat]": "{}".format(trans_fat),
            "nutritional_content[protein]": "{}".format(protein),
            "nutritional_content[cholesterol]": "{}".format(cholesterol),
            "nutritional_content[vitamin_a]": "{}".format(vitamin_a),
            "nutritional_content[calcium]": "{}".format(calcium),
            "nutritional_content[vitamin_c]": "{}".format(vitamin_c),
            "nutritional_content[iron]": "{}".format(iron),
            "food_entry[quantity]": "1.0",
            "food_entry[meal_id]": "0",
            "addtodiary": "no",
            "preserve_exact_description_and_brand": "true",
            "continue": "Save"
        }
        # Make entry public if requested, Hint: submit "sharefood": 0 also generates a public db entry, so only add
        # "sharefood"" if really requested
        if sharepublic:
            data["sharefood"] = 1

        submit4_url = parse.urljoin(self.BASE_URL_SECURE, self.SUBMIT_POST_PATH)
        result = self.session.post(submit4_url, data, )
        if result.status_code == 200:
            document = lxml.html.document_fromstring(result.content.decode('utf-8'))
            try:
                if not document.xpath(
                        # If list is empty there should be no error, could be replaced with assert
                        "//*[@id='errorExplanation']/ul/li"):
                    return True
                    # print("No Error :)")
                    # Would like to return FoodItem, but seems that it take
                    # to long until the submitted food is available in the DB
                    # return self.get_food_search_results("{} {}".format(brand, description))[0]
                else:  # Error occurred
                    error = document.xpath("//*[@id='errorExplanation']/ul/li")[0].text
                    error = error.replace("Description ", "")  # For cosmetic reasons
                    raise MyfitnesspalRequestFailed(
                        "Unable to submit food to MyFitnessPal: {}".format(error)
                    )
            except:
                logger.warning("Unable to submit food to MyFitnessPal: {}".format(error))

        elif not result.ok:
            logger.warning(
                "Request Error - Unable to submit food to MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )
            return None

    def set_new_goal(self, energy: float = "", energy_unit: str = "", carbohydrates: float = "", protein: float = "",
                     fat: float = "",
                     percent_carbohydrates: float = "", percent_protein: float = "", percent_fat: float = "",
                     saturated_fat: float = "",
                     polyunsaturated_fat: float = "",
                     monounsaturated_fat: float = "",
                     trans_fat: float = "",
                     fiber: float = "",
                     sugar: float = "",
                     cholesterol: float = "",
                     sodium: float = "",
                     potassium: float = "",
                     vitamin_a: float = "",
                     vitamin_c: float = "",
                     calcium: float = "",
                     iron: float = "",
                     assign_exercise_energy="nutrient_goal"):
        """Function to update your nutrition goals. Function will return True if successful."""
        # FROM MFP JS:
        #       var calculated_energy = 4 * parseFloat(this.get('carbGrams')) + 4 * parseFloat(this.get('proteinGrams')) + 9 * parseFloat(this.get('fatsGrams'));

        # Get User Default Unit Preference
        if energy_unit != "calories" and energy_unit != "kilojoules":
            energy_unit = self.user_metadata['unit_preferences']['energy']

        # Step 1 to get Authenticity Token and current values
        submit1_url = parse.urljoin(self.BASE_URL_SECURE, "account/my_goals")
        now = datetime.datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        document = self._get_document_for_url(submit1_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]")

        # Build  Header for API-Requests
        auth_header = self.session.headers
        auth_header['authorization'] = f"Bearer {self.access_token}"
        auth_header['mfp-client-id'] = "mfp-main-js"
        auth_header['mfp-user-id'] = f"{self.user_id}"

        # Get Request
        old_goals_document = self.session.get(f"https://api.myfitnesspal.com/v2/nutrient-goals?date={today}",
                                              headers=auth_header)
        old_goals = json.loads(old_goals_document.text)

        # Marcro Calculation
        # If no macro goals were provided calculate them with percentage value
        if carbohydrates == "" or protein == "" or fat == "":
            # If even no macro percentages values were provided calculate them from old values
            if percent_carbohydrates == "" or percent_protein == "" or percent_fat == "":
                old_energy_value = old_goals['items'][0]['default_goal']['energy']['value']
                old_energy_unit = old_goals['items'][0]['default_goal']['energy']['unit']
                old_carbohydrates = old_goals['items'][0]['default_goal']['carbohydrates']
                old_fat = old_goals['items'][0]['default_goal']['fat']
                old_protein = old_goals['items'][0]['default_goal']['protein']

                # If old and new values are in diffrent units then convert old value to new unit
                if not old_energy_unit == energy_unit:
                    if old_energy_unit == "kilojoules" and energy_unit == "calories":
                        old_energy_value *= 0.2388
                        old_energy_unit = "calories"
                    elif old_energy_unit == "calories" and energy_unit == "kilojoules":
                        """ FROM MFP JS
                        if (energyUnit === 'kilojoules') {
                            calories *= 4.184;
                        }
                        """
                        old_energy_value *= 4.184
                        old_energy_unit = "kilojoules"
                    else:
                        raise ValueError

                ####
                carbohydrates = energy * old_carbohydrates / old_energy_value
                protein = energy * old_protein / old_energy_value
                fat = energy * old_fat / old_energy_value
            # If percentage values were provided check
            else:
                carbohydrate = energy * percent_carbohydrates / 100 / 4
                protein = energy * percent_protein / 100 / 4
                fat = energy * percent_fat / 100 / 9
                if energy_unit == "kilojoules":
                    carbohydrates = round(carbohydrates / 4.184, 2)
                    protein = round(protein / 4.184, 2)
                    fat = round(fat / 4.184, 2)
        else:
            macro_energy = carbohydrates * 4 + protein * 4 + fat * 9
            if energy_unit == "kilojoules":
                macro_energy *= 4.184
            # Compare energy values and set it correctly due to macros. Will also fix if no energy_value was provided.
            if energy != macro_energy:
                logger.warning(
                    "Provided energy value and calculated engery value from macros does not match! Will Override!")
                energy = macro_energy
            # TODO Calculate if no energy were provided

            pass

        # Build payload based on observed browser behaviour
        # TODO Inser additional micro nurtitions
        new_goals = {}
        new_goals['item'] = old_goals['items'][0]

        new_goals['item'].pop('valid_to', None)
        new_goals['item'].pop('default_group_id', None)
        new_goals['item'].pop('updated_at', None)
        new_goals['item']['default_goal']['meal_goals'] = []
        new_goals['item']['default_goal'].pop('exercise_carbohydrates_percentage', None)
        new_goals['item']['default_goal'].pop('exercise_fat_percentage', None)
        new_goals['item']['default_goal'].pop('exercise_protein_percentage', None)
        new_goals['item']['default_goal'].pop('exercise_saturated_fat_percentage', None)
        new_goals['item']['default_goal'].pop('exercise_sugar_percentage', None)

        # insert new values
        new_goals['item']['valid_from'] = today

        new_goals['item']['default_goal']['energy']['value'] = energy
        new_goals['item']['default_goal']['energy']['unit'] = energy_unit
        new_goals['item']['default_goal']['carbohydrates'] = carbohydrates
        new_goals['item']['default_goal']['protein'] = protein
        new_goals['item']['default_goal']['fat'] = fat

        for i in new_goals['item']['daily_goals']:
            """new_goals['item']['daily_goals'][i]['meal_goals'] = []
            new_goals['item']['daily_goals'][i].pop('group_id', None)
            new_goals['item']['daily_goals'][i].pop('exercise_carbohydrates_percentage', None)
            new_goals['item']['daily_goals'][i].pop('exercise_fat_percentage', None)
            new_goals['item']['daily_goals'][i].pop('exercise_protein_percentage', None)
            new_goals['item']['daily_goals'][i].pop('exercise_saturated_fat_percentage', None)
            new_goals['item']['daily_goals'][i].pop('exercise_sugar_percentage', None)"""
            i['meal_goals'] = []
            i.pop('group_id', None)
            i.pop('exercise_carbohydrates_percentage', None)
            i.pop('exercise_fat_percentage', None)
            i.pop('exercise_protein_percentage', None)
            i.pop('exercise_saturated_fat_percentage', None)
            i.pop('exercise_sugar_percentage', None)

            # insert new values
            i['energy']['value'] = energy
            i['energy']['unit'] = energy_unit
            i['carbohydrates'] = carbohydrates
            i['protein'] = protein
            i['fat'] = fat

        # Build Post-Request
        # Post Request
        result = self.session.post(f"https://api.myfitnesspal.com/v2/nutrient-goals", json.dumps(new_goals),
                                   headers=auth_header)

        # TODO Check Request Result
        if result.status_code == 200:
            return True
        elif not result.ok:
            logger.warning(
                "Request Error - Unable to submit Goals to MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )
            return None
        else:
            logger.error(
                "Request Error - Unable to submit Goals to MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )
            print(result)
            return None

    def get_recipe_list(self):
        # TODO EXCEPTION HANDLING
        recipes_dict = {}

        page_count = 1
        next_page = True
        while (next_page):
            RECIPES_PATH = f"recipe_parser?page={page_count}&sort_order=recent"
            recipes_url = parse.urljoin(self.BASE_URL_SECURE, RECIPES_PATH)
            document = self._get_document_for_url(recipes_url)
            recipes = document.xpath("//*[@id='main']/ul[1]/li")  # get all items in the recipe list
            for recipe_info in recipes:
                recipe_path = recipe_info.xpath("./div[2]/h2/span[1]/a")[0].attrib["href"]
                recipe_id = recipe_path.split("/")[-1]
                recipe_title = recipe_info.xpath("./div[2]/h2/span[1]/a")[0].attrib["title"]
                recipes_dict[recipe_id] = recipe_title

            # Check for Pagination
            pagination_links = document.xpath('//*[@id="main"]/ul[2]/a')
            if (pagination_links):
                if (
                        page_count == 1):  # If Pagination exists and it is page 1 there have to be a second, but only one href to the next (obviously none to the previous)
                    page_count += 1
                elif (len(pagination_links) > 1):  # If there are two links, ont to the previous and one to the next
                    page_count += 1
                else:
                    next_page = False  # Only one link means it is the last page

        print(recipes_dict.values())
        return recipes_dict

    def get_recipe(self, recipeid: int):
        # TODO EXCEPTION HANDLING
        recipe_PATH = f"/recipe/view/{recipeid}"
        recipe_url = parse.urljoin(self.BASE_URL_SECURE, recipe_PATH)
        document = self._get_document_for_url(recipe_url)

        recipe_dict = {}
        recipe_dict['id'] = recipeid
        recipe_dict['title'] = document.xpath('//*[@id="main"]/div[3]/div[2]/h1')[0].text
        recipe_dict['servings'] = document.xpath('//*[@id="recipe_servings"]')[0].text

        recipe_dict['ingridients'] = []
        ingridients = document.xpath('//*[@id="main"]/div[4]/div/*/li')
        for ingridient in ingridients:
            tmp = {}
            tmp['title'] = ingridient.text.strip(" \n")
            recipe_dict['ingridients'].append(tmp)

        recipe_dict['nutrition'] = {}
        recipe_dict['nutrition']['energy'] = document.xpath('//*[@id="main"]/div[3]/div[2]/div[2]/div')[0].text.strip(
            " \n")
        recipe_dict['nutrition']['carbohydrates'] = document.xpath('//*[@id="carbs"]/td[1]/span[2]')[0].text.strip(
            " \n")
        recipe_dict['nutrition']['fiber'] = document.xpath('//*[@id="fiber"]/td[1]/span[2]')[0].text.strip(" \n")
        recipe_dict['nutrition']['sugar'] = document.xpath('//*[@id="sugar"]/td[1]/span[2]')[0].text.strip(" \n")
        recipe_dict['nutrition']['protein'] = document.xpath('//*[@id="protein"]/td[1]/span[2]')[0].text.strip(" \n")
        recipe_dict['nutrition']['fat'] = document.xpath('//*[@id="total_fat"]/td[1]/span[2]')[0].text.strip(" \n")
        recipe_dict['nutrition']['saturated_fat'] = document.xpath('//*[@id="saturated_fat"]/td[1]/span[2]')[
            0].text.strip(" \n")
        recipe_dict['nutrition']['monounsaturated_fat'] = \
            document.xpath('//*[@id="monounsaturated_fat"]/td[1]/span[2]')[0].text.strip(" \n")
        recipe_dict['nutrition']['polyunsaturated_fat'] = \
            document.xpath('//*[@id="polyunsaturated_fat"]/td[1]/span[2]')[0].text.strip(" \n")
        recipe_dict['nutrition']['trans_fat'] = document.xpath('//*[@id="trans_fat"]/td[1]/span[2]')[0].text.strip(
            " \n")

        return recipe_dict

    def get_meal_list(self):
        # TODO EXCEPTION HANDLING
        meals_dict = {}
        MEALS_PATH = f"meal/mine"
        meals_url = parse.urljoin(self.BASE_URL_SECURE, MEALS_PATH)
        document = self._get_document_for_url(meals_url)
        meals = document.xpath("//*[@id='matching']/li")  # get all items in the recipe list
        for meal in meals:
            meal_path = meal.xpath("./a")[0].attrib["href"]
            meal_id = meal_path.split("/")[-1].split("?")[0]
            meal_title = meal.xpath("./a")[0].text
            meals_dict[meal_id] = meal_title

        print(meals_dict.values())
        return meals_dict

    def get_meal(self, mealid: int, meal_title: str):
        # TODO EXCEPTION HANDLING
        meal_dict = {}
        meal_dict['id'] = mealid
        meal_dict['title'] = meal_title
        meal_dict['ingridients'] = []
        meal_dict['nutrition'] = {}
        meal_dict['nutrition']['energy'] = ""
        meal_dict['nutrition']['carbohydrates'] = ""
        meal_dict['nutrition']['protein'] = ""
        meal_dict['nutrition']['fat'] = ""
        meal_dict['nutrition']['sugar'] = ""

        MEAL_PATH = f"/meal/update_meal_ingredients/{mealid}"
        meal_url = parse.urljoin(self.BASE_URL_SECURE, MEAL_PATH)
        document = self._get_document_for_url(meal_url)
        ingridients = document.xpath('//*[@id="meal-table"]/tbody/tr')

        for ingridient in ingridients:
            tmp = {}
            tmp['title'] = ingridient.xpath('./td[1]')[0].text
            tmp['nutrition'] = {}
            tmp['nutrition']['energy'] = ingridient.xpath('./td[2]')[0].text
            tmp['nutrition']['carbohydrates'] = ingridient.xpath('./td[3]')[0].text
            tmp['nutrition']['protein'] = ingridient.xpath('./td[5]')[0].text
            tmp['nutrition']['fat'] = ingridient.xpath('./td[4]')[0].text
            tmp['nutrition']['sugar'] = ingridient.xpath('./td[7]')[0].text
            tmp['nutrition']['sodium'] = ingridient.xpath('./td[6]')[0].text
            meal_dict['ingridients'].append(tmp)

        total = document.xpath('//*[@id="mealTableTotal"]/tbody/tr')[0]
        meal_dict['nutrition']['energy'] = total.xpath('./td[2]')[0].text
        meal_dict['nutrition']['carbohydrates'] = total.xpath('./td[3]')[0].text
        meal_dict['nutrition']['protein'] = total.xpath('./td[5]')[0].text
        meal_dict['nutrition']['fat'] = total.xpath('./td[4]')[0].text
        meal_dict['nutrition']['sugar'] = total.xpath('./td[7]')[0].text
        meal_dict['nutrition']['sodium'] = total.xpath('./td[6]')[0].text

        return meal_dict