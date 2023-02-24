Accessing a Friend’s Diary (Shared)
===================================

If a friend has their diary visibility set to "Friends Only", you can grab their
diary entries.

To access a single day’s information:

.. code:: python

    import myfitnesspal

    client = myfitnesspal.Client()

    friend_day = client.get_date(2020, 8, 23, friend_username="username_of_my_friend")

    friend_day
    # >> <03/02/13 {'sodium': 3326, 'carbohydrates': 369, 'calories': 2001, 'fat': 22, 'sugar': 103, 'protein': 110}>

    friend_day.totals
    # >> {'calories': 2001,
    #     'carbohydrates': 369,
    #     'fat': 22,
    #     'protein': 110,
    #     'sodium': 3326,
    #     'sugar': 103}

    friend_day.meals
    # >> [<Breakfast {}>,
    #    <Lunch {'sodium': 712, 'carbohydrates': 106, 'calories': 485, 'fat': 3, 'sugar': 0, 'protein': 17}>,
    #    <Dinner {'sodium': 2190, 'carbohydrates': 170, 'calories': 945, 'fat': 11, 'sugar': 17, 'protein': 53}>,
    #    <Snacks {'sodium': 424, 'carbohydrates': 93, 'calories': 571, 'fat': 8, 'sugar': 86, 'protein': 40}>]


To access a week’s information with a loop on a date range:

.. code:: python

    import datetime

    start_date = datetime.date(2023, 2, 18)
    end_date = datetime.date(2023, 2, 25)

    friend_shared_diary_data = []

    for day in range(int((end_date - start_date).days)):
        loop_year=((start_date + datetime.timedelta(day)).strftime("%Y"))
        loop_month=((start_date + datetime.timedelta(day)).strftime("%m"))
        loop_day=((start_date + datetime.timedelta(day)).strftime("%d"))
        loop_pretty_date=str(start_date + datetime.timedelta(day))
        diary_day_data = client.get_date(loop_year, loop_month, loop_day, friend_username="username_of_my_friend")
        friend_shared_diary_data.append({loop_pretty_date: diary_day_data.totals})

    print(friend_shared_diary_data)
