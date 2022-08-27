Accessing your Exercises
========================

Exercises are accessed through the ``day.exercises`` command - giving an
2-item array of ``[<Cardiovascular>, <Strength>]``, which can be
explored using ``get_as_list()``

To get a list of cardiovascular exercises

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   day = client.get_date(2019, 3, 12)

   day.exercises[0].get_as_list()
   # >> [{'name': 'Walking, 12.5 mins per km, mod. pace, walking dog', 'nutrition_information': {'minutes': 60, 'calories burned': 209}}, {'name': 'Running (jogging), 8 kph (7.5 min per km)', 'nutrition_information': {'minutes': 25, 'calories burned': 211}}]

And then access individual properties

.. code:: python

   day.exercises[0].get_as_list()[0]['name']

   # >> 'Walking, 12.5 mins per km, mod. pace, walking dog'

   day.exercises[0].get_as_list()[0]['nutrition_information']['minutes']
   # >> 60

   day.exercises[0].get_as_list()[0]['nutrition_information']['calories burned']
   # >> 209

To get a list of strength exercises

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   day = client.get_date(2019, 3, 12)

   day.exercises[1].get_as_list()
   # >> [{'name': 'Leg Press', 'nutrition_information': {'sets': 3, 'reps/set': 12, 'weight/set': 20}}, {'name': 'Seated Row, Floor, Machine', 'nutrition_information': {'sets': 3, 'reps/set': 12, 'weight/set': 20}}]

And then access individual properties

.. code:: python

   day.exercises[1].get_as_list()[0]['name']
   # >> 'Leg Press'

   day.exercises[1].get_as_list()[0]['nutrition_information']['sets']
   # >> 3

   day.exercises[1].get_as_list()[0]['nutrition_information']['reps/set']
   # >> 12

   day.exercises[1].get_as_list()[0]['nutrition_information']['weight/set']
   # >> 20
