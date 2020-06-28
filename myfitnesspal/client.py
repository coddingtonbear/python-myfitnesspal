import datetime
import logging
import re
from collections import OrderedDict

import lxml.html
import requests
from measurement.measures import Energy, Mass, Volume
from six.moves.urllib import parse

from .base import MFPBase
from .day import Day
from .entry import Entry
from .exercise import Exercise
from .fooditem import FoodItem
from .fooditemserving import FoodItemServing
from .keyring_utils import get_password_from_keyring
from .meal import Meal
from .note import Note

logger = logging.getLogger(__name__)

BRITISH_UNIT_MATCHER = re.compile(r"(?:(?P<st>\d+) st)\W*(?:(?P<lbs>\d+) lb)?")


class Client(MFPBase):
    BASE_URL = "http://www.myfitnesspal.com/"
    BASE_URL_SECURE = "https://www.myfitnesspal.com/"
    BASE_API_URL = "https://api.myfitnesspal.com/"
    LOGIN_PATH = "account/login"
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
    }

    def __init__(self, username, password=None, login=True, unit_aware=False):
        self.provided_username = username
        if password is None:
            password = get_password_from_keyring(username)
        self.__password = password
        self.unit_aware = unit_aware

        self._user_metadata = {}
        self._auth_data = {}

        self.session = requests.Session()
        if login:
            self._login()

    @property
    def user_id(self):
        return self._auth_data["user_id"]

    @property
    def user_metadata(self):
        return self._user_metadata

    @property
    def access_token(self):
        return self._auth_data["access_token"]

    @property
    def effective_username(self):
        """ One's actual username may be different from the one used for login

        This method will return the actual username if it is available, but
        will fall back to the one provided if it is not.

        """
        if self.user_metadata:
            return self.user_metadata["username"]
        return self.provided_username

    def _login(self):
        login_url = parse.urljoin(self.BASE_URL_SECURE, self.LOGIN_PATH)
        document = self._get_document_for_url(login_url)
        authenticity_token = document.xpath(
            "(//input[@name='authenticity_token']/@value)[1]"
        )[0]
        utf8_field = document.xpath("(//input[@name='utf8']/@value)[1]")[0]

        result = self.session.post(
            login_url,
            data={
                "utf8": utf8_field,
                "authenticity_token": authenticity_token,
                "username": self.effective_username,
                "password": self.__password,
            },
        )
        # result.content is bytes so we decode it ASSUMING utf8 (which may be a
        # bad assumption?) PORTING_CHECK
        content = result.content.decode("utf8")
        if "Incorrect username or password" in content:
            raise ValueError("Incorrect username or password.")

        self._auth_data = self._get_auth_data()
        self._user_metadata = self._get_user_metadata()

        # authenticity token required for measurement set function.
        self._authenticity_token = authenticity_token

    def _get_auth_data(self):
        result = self._get_request_for_url(
            parse.urljoin(self.BASE_URL_SECURE, "/user/auth_token") + "?refresh=true"
        )
        if not result.ok:
            raise RuntimeError(
                "Unable to fetch authentication token from MyFitnessPal: "
                "status code: {status}".format(status=result.status_code)
            )

        return result.json()

    def _get_user_metadata(self):
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
            [("fields[]", name,) for name in requested_fields]
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

    def _get_full_name(self, raw_name):
        name = raw_name.lower().strip()
        if name not in self.ABBREVIATIONS:
            return name
        return self.ABBREVIATIONS[name]

    def _get_url_for_date(self, date, username):
        date_str = date.strftime("%Y-%m-%d")
        return (
            parse.urljoin(self.BASE_URL_SECURE, "food/diary/" + username)
            + f"?date={date_str}"
        )

    def _get_url_for_measurements(self, page=1, measurement_id=1):
        return (
            parse.urljoin(self.BASE_URL_SECURE, "measurements/edit")
            + f"?page={page}&type={measurement_id}"
        )

    def _get_request_for_url(self, url, send_token=False, headers=None, **kwargs):
        if headers is None:
            headers = {}

        if send_token:
            headers.update(
                {
                    "Authorization": f"Bearer {self.access_token}",
                    "mfp-client-id": "mfp-main-js",
                    "mfp-user-id": self.user_id,
                }
            )

        return self.session.get(url, headers=headers, **kwargs)

    def _get_content_for_url(self, *args, **kwargs):
        return self._get_request_for_url(*args, **kwargs).content.decode("utf8")

    def _get_document_for_url(self, url):
        content = self._get_content_for_url(url)

        return lxml.html.document_fromstring(content)

    def _get_measurement(self, name, value):
        if not self.unit_aware:
            return value
        measure, kwarg = self.DEFAULT_MEASURE_AND_UNIT[name]
        return measure(**{kwarg: value})

    def _get_numeric(self, string, data_type=int):
        value = re.sub(r"[^\d.]+", "", string)

        matched = BRITISH_UNIT_MATCHER.match(string)
        if matched:
            value = int(matched.groupdict()["lbs"] or 0) + (
                int(matched.groupdict()["st"] or 0) * 14
            )

        try:
            return data_type(value)
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

    def _get_completion(self, document):
        try:
            completion_header = document.xpath("//div[@id='complete_day']")[0]
            completion_message = completion_header.getchildren()[0]

            if "day_incomplete_message" in completion_message.classes:
                return False
            elif "day_complete_message" in completion_message.classes:
                return True
        except IndexError:
            return False  # Who knows, probably not my diary.

    def _get_meals(self, document):
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

                entries.append(Entry(name, nutrition,))

            meals.append(Meal(meal_name, entries,))

        return meals

    def _get_url_for_exercise(self, date, username):
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

                entries.append(Entry(name, attrs,))
                row = row.getnext()

            exercises.append(Exercise(ex_name, entries,))

        return exercises

    def _get_exercises(self, *args, **kwargs):
        if len(args) == 3:
            date = datetime.date(int(args[0]), int(args[1]), int(args[2]),)
        elif len(args) == 1 and isinstance(args[0], datetime.date):
            date = args[0]
        else:
            raise ValueError(
                "get_exercise accepts either a single datetime "
                "or date instance, or three integers representing "
                "year, month, and day respectively."
            )

        # get the exercise URL
        document = self._get_document_for_url(
            self._get_url_for_exercise(
                date, kwargs.get("username", self.effective_username)
            )
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

    def get_date(self, *args, **kwargs):
        if len(args) == 3:
            date = datetime.date(int(args[0]), int(args[1]), int(args[2]),)
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
    ):
        """ Returns measurements of a given name between two dates."""
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

    def set_measurements(self, measurement="Weight", value=None, date=None):
        """ Sets measurement for today's date."""
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

        # gather the IDs for all measurement types
        measurement_ids = self._get_measurement_ids(document)

        # check if the measurement exists before going too far
        if measurement not in measurement_ids.keys():
            raise ValueError(f"Measurement '{measurement}' does not exist.")

        # build the update url.
        update_url = parse.urljoin(self.BASE_URL_SECURE, "measurements/new")

        # setup a dict for the post
        data = {
            "authenticity_token": self._authenticity_token,
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
            raise RuntimeError(
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
            ] = self._get_numeric(measurements[date], data_type=float)

        measurements = temp_measurements

        return measurements

    def _get_measurement_ids(self, document):

        # find the option element for all of the measurement choices
        options = document.xpath("//select[@id='type']/option")

        ids = {}

        # create a dictionary out of the text and value of each choice
        for option in options:
            ids[option.text] = int(option.attrib.get("value"))

        return ids

    def get_measurement_id_options(self):
        """ Returns list of measurement choices."""
        # get the URL for the main check in page
        document = self._get_document_for_url(self._get_url_for_measurements())

        # gather the IDs for all measurement types
        measurement_ids = self._get_measurement_ids(document)
        return measurement_ids

    def _get_notes(self, date):
        result = self._get_request_for_url(
            parse.urljoin(self.BASE_URL_SECURE, "/food/note",)
            + "?date={date}".format(date=date.strftime("%Y-%m-%d"))
        )
        return Note(result.json()["item"])

    def _get_water(self, date):
        result = self._get_request_for_url(
            parse.urljoin(self.BASE_URL_SECURE, "/food/water",)
            + "?date={date}".format(date=date.strftime("%Y-%m-%d"))
        )
        value = result.json()["item"]["milliliters"]
        if not self.unit_aware:
            return value

        return Volume(ml=value)

    def __str__(self):
        return f"MyFitnessPal Client for {self.effective_username}"

    def get_food_search_results(self, query):
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
            raise ValueError("Unable to load search results.")

        return self._get_food_search_results(document)

    def _get_food_search_results(self, document):
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
            serving = nutr_info[-2].strip()
            calories = float(nutr_info[-1].replace("calories", "").strip())
            items.append(FoodItem(mfp_id, mfp_name, brand, verif, serving, calories,))

        return items

    def get_food_item_details(self, mfp_id):
        # api call for food item's details
        requested_fields = [
            "nutritional_contents",
            "serving_sizes",
            "confirmations",
        ]
        query_string = parse.urlencode(
            [("fields[]", name,) for name in requested_fields]
        )
        metadata_url = (
            parse.urljoin(self.BASE_API_URL, f"/v2/foods/{mfp_id}") + "?" + query_string
        )
        result = self._get_request_for_url(metadata_url, send_token=True)
        if not result.ok:
            logger.warning(
                "Unable to fetch item details; this may cause Myfitnesspal "
                "to behave incorrectly if you have logged-in with your "
                "e-mail address rather than your basic username; status %s.",
                result.status_code,
            )
        resp = result.json()["item"]

        # identifying serving info
        servings = []
        default_serving = None
        for s in resp["serving_sizes"]:
            serving = FoodItemServing(
                s["id"], s["nutrition_multiplier"], s["value"], s["unit"], s["index"],
            )
            servings.append(serving)
            if serving.index == 0:
                default_serving = serving.unit

        # identifying calories for default serving
        nutr_info = resp["nutritional_contents"]
        if "energy" in nutr_info:
            calories = nutr_info["energy"]["value"]
        else:
            calories = 0.0

        # returning food item's details
        return FoodItem(
            mfp_id,
            resp["description"],
            resp.get("brand_name"),
            resp["verified"],
            default_serving,
            calories,
            calcium=nutr_info.get("calcium", 0.0),
            carbohydrates=nutr_info.get("carbohydrates", 0.0),
            cholesterol=nutr_info.get("cholesterol", 0.0),
            fat=nutr_info.get("fat", 0.0),
            fiber=nutr_info.get("fiber", 0.0),
            iron=nutr_info.get("iron", 0.0),
            monounsaturated_fat=nutr_info.get("monounsaturated_fat", 0.0),
            polyunsaturated_fat=nutr_info.get("polyunsaturated_fat", 0.0),
            potassium=nutr_info.get("potassium", 0.0),
            protein=nutr_info.get("protein", 0.0),
            saturated_fat=nutr_info.get("saturated_fat", 0.0),
            sodium=nutr_info.get("sodium", 0.0),
            sugar=nutr_info.get("sugar", 0.0),
            trans_fat=nutr_info.get("trans_fat", 0.0),
            vitamin_a=nutr_info.get("vitamin_a", 0.0),
            vitamin_c=nutr_info.get("vitamin_c", 0.0),
            confirmations=resp["confirmations"],
            servings=servings,
        )
