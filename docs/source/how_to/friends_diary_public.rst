Accessing a Friend’s Diary
==========================

If a friend has their diary visibility set to "Public", you can grab their
diary entries:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   friend_day = client.get_date(2020, 8, 23, username="username_of_my_friend")
   >>> friend_day
   <08/23/20 {'calories': 891.0, 'carbohydrates': 105.0, 'fat': 38.0, 'protein': 29.0, 'sodium': 0.0, 'sugar': 2.0}>
