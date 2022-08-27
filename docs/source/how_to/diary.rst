Accessing your Diary
====================

To access a single day’s information:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   day = client.get_date(2013, 3, 2)
   day
   # >> <03/02/13 {'sodium': 3326, 'carbohydrates': 369, 'calories': 2001, 'fat': 22, 'sugar': 103, 'protein': 110}>

To see all meals you can use the Day object’s ``meals`` property:

.. code:: python

   day.meals
   # >> [<Breakfast {}>,
   #    <Lunch {'sodium': 712, 'carbohydrates': 106, 'calories': 485, 'fat': 3, 'sugar': 0, 'protein': 17}>,
   #    <Dinner {'sodium': 2190, 'carbohydrates': 170, 'calories': 945, 'fat': 11, 'sugar': 17, 'protein': 53}>,
   #    <Snacks {'sodium': 424, 'carbohydrates': 93, 'calories': 571, 'fat': 8, 'sugar': 86, 'protein': 40}>]

To access dinner, you can access it by its index in ``day.meals``:

.. code:: python

   dinner = day.meals[2]
   dinner
   # >> <Dinner {'sodium': 2190, 'carbohydrates': 170, 'calories': 945, 'fat': 11, 'sugar': 17, 'protein': 53}>

To get a list of things you ate for dinner, I can use the dinner Meal
object’s ``entries`` property:

.. code:: python

   dinner.entries
   # >> [<Montebello - Spaghetti noodles, 6 oz. {'sodium': 0, 'carbohydrates': 132, 'calories': 630, 'fat': 3, 'sugar': 3, 'protein': 21}>,
   #     <Fresh Market - Arrabiatta Organic Pasta Sauce, 0.5 container (3 cups ea.) {'sodium': 1410, 'carbohydrates': 24, 'calories': 135, 'fat': 5, 'sugar': 12, 'protein': 6}>,
   #     <Quorn - Meatless and Soy-Free Meatballs, 6 -4 pieces (68g) {'sodium': 780, 'carbohydrates': 14, 'calories': 180, 'fat': 3, 'sugar': 2, 'protein': 26}>]

To access one of the items, use the entries property as a list:

.. code:: python

   spaghetti = dinner.entries[0]
   spaghetti.name
   # >> Montebello - Spaghetti noodles, 6 oz.

For a daily summary of your nutrition information, you can use a Day
object’s ``totals`` property:

.. code:: python

   day.totals
   # >> {'calories': 2001,
   #     'carbohydrates': 369,
   #     'fat': 22,
   #     'protein': 110,
   #     'sodium': 3326,
   #     'sugar': 103}

Or, if you just want to see how many milliliters of water you’ve
recorded, or the notes you’ve entered for a day:

.. code:: python

   day.water
   # >> 1
   day.notes
   # >> "This is the note I entered for this day"

For just one meal:

.. code:: python

   dinner.totals
   # >> {'calories': 945,
   #     'carbohydrates': 170,
   #     'fat': 11,
   #     'protein': 53,
   #     'sodium': 2190,
   #     'sugar': 17}

For just one entry:

.. code:: python

   spaghetti.totals
   # >> {'calories': 630,
   #     'carbohydrates': 132,
   #     'fat': 3,
   #     'protein': 21,
   #     'sodium': 0,
   #     'sugar': 3}

Hints
-----

Day objects act as dictionaries:

.. code:: python

   day.keys()
   # >> ['Breakfast', 'Lunch', 'Dinner', 'Snack']
   lunch = day['Lunch']
   print lunch
   # >> [<Generic - Ethiopian - Miser Wat (Red Lentils), 2 cup {'sodium': 508, 'carbohydrates': 76, 'calories': 346, 'fat': 2, 'sugar': 0, 'protein': 12}>,
   #     <Injera - Ethiopian Flatbread, 18 " diameter {'sodium': 204, 'carbohydrates': 30, 'calories': 139, 'fat': 1, 'sugar': 0, 'protein': 5}>]

Meal objects act as lists:

.. code:: python

   len(lunch)
   # >> 2
   miser_wat = lunch[0]
   print miser_wat
   # >> <Generic - Ethiopian - Miser Wat (Red Lentils), 2 cup {'sodium': 508, 'carbohydrates': 76, 'calories': 346, 'fat': 2, 'sugar': 0, 'protein': 12}>

and Entry objects act as dictionaries:

.. code:: python

   print miser_wat['calories']
   # >> 346

and, since the measurement units returned are not necessarily very intuitive,
you can enable or disable unit awareness using the `unit_aware` keyword
argument.

.. code:: python

   client = myfitnesspal.Client(unit_aware=True)
   day = client.get_date(2013, 3, 2)
   lunch = day['lunch']
   print lunch
   # >> [<Generic - Ethiopian - Miser Wat (Red Lentils), 2 cup {'sodium': Weight(mg=508), 'carbohydrates': Weight(g=76), 'calories': Energy(Calorie=346), 'fat': Weight(g=2), 'sugar': Weight(g=0), 'protein': Weight(g=12)}>,
   miser_wat = lunch[0]
   print miser_wat['calories']
   # >> Energy(Calorie=346)
