from __future__ import print_function
from datetime import datetime as dt
from datetime import timedelta as td
import argparse
import myfitnesspal

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("username", type=str, help="MyFitnessPal username (string)")
    parser.add_argument("password", type=str, help="MyFitnessPal password (string)")
    args = parser.parse_args()

    client = myfitnesspal.Client(args.username, args.password)

    today = dt.today()
    print("Investigating today's entries:", today)
    day = client.get_date(today)

    print("Day", day)
    print("Meals", day.meals)
    breakfast = day.meals[0]
    print("Breakfast", breakfast)
    print("Breakfast entries", breakfast.entries)

    print("Totals", day.totals)
    print("Water", day.water)
    print("Notes", day.notes)
    print("Keys for today", day.keys())

    print("----")
    for day_offset in range(7):
        td_day = td(hours=24*day_offset)
        a_day = today - td_day
        day = client.get_date(a_day)
        print("Fetching", a_day)
        print("Day", day)

