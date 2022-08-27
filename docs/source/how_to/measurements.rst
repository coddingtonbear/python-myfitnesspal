Accessing your Measurements
===========================

To access measurements from the past 30 days:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   weight = client.get_measurements('Weight')
   weight
   # >> OrderedDict([(datetime.date(2015, 5, 14), 171.0), (datetime.date(2015, 5, 13), 173.8), (datetime.date(2015, 5,12), 171.8),
   #                 (datetime.date(2015, 5, 11), 171.6), (datetime.date(2015, 5, 10), 172.4), (datetime.date(2015, 5, 9), 170.2),
   #                 (datetime.date(2015, 5, 8), 171.0),  (datetime.date(2015, 5, 7), 171.2),  (datetime.date(2015, 5, 6), 170.8),
   #                 (datetime.date(2015, 5, 5), 171.8),  (datetime.date(2015, 5, 4), 174.2),  (datetime.date(2015, 5, 3), 172.2),
   #                 (datetime.date(2015, 5, 2), 171.0),  (datetime.date(2015, 5, 1), 171.2),  (datetime.date(2015, 4, 30), 171.6),
   #                 (datetime.date(2015, 4, 29), 172.4), (datetime.date(2015, 4, 28), 172.2), (datetime.date(2015, 4, 27), 173.2),
   #                 (datetime.date(2015, 4, 26), 171.8), (datetime.date(2015, 4, 25), 170.8), (datetime.date(2015, 4, 24), 171.2),
   #                 (datetime.date(2015, 4, 23), 171.6), (datetime.date(2015, 4, 22), 173.2), (datetime.date(2015, 4, 21), 174.2),
   #                 (datetime.date(2015, 4, 20), 173.6), (datetime.date(2015, 4, 19), 171.8), (datetime.date(2015, 4, 18), 170.4),
   #                 (datetime.date(2015, 4, 17), 169.8), (datetime.date(2015, 4, 16), 170.4), (datetime.date(2015, 4, 15), 170.8),
   #                 (datetime.date(2015, 4, 14), 171.6)])

To access measurements since a given date:

.. code:: python

   import datetime

   may = datetime.date(2015, 5, 1)

   body_fat = client.get_measurements('Body Fat', may)
   body_fat
   # >> OrderedDict([(datetime.date(2015, 5, 14), 12.8), (datetime.date(2015, 5, 13), 13.1), (datetime.date(2015, 5, 12), 12.7),
   #                 (datetime.date(2015, 5, 11), 12.7), (datetime.date(2015, 5, 10), 12.8), (datetime.date(2015, 5, 9), 12.4),
   #                 (datetime.date(2015, 5, 8), 12.6),  (datetime.date(2015, 5, 7), 12.7),  (datetime.date(2015, 5, 6), 12.6),
   #                 (datetime.date(2015, 5, 5), 12.9),  (datetime.date(2015, 5, 4), 13.0),  (datetime.date(2015, 5, 3), 12.6),
   #                 (datetime.date(2015, 5, 2), 12.6),  (datetime.date(2015, 5, 1), 12.7)])

To access measurements within a date range:

.. code:: python

   thisweek = datetime.date(2015, 5, 11)
   lastweek = datetime.date(2015, 5, 4)

   weight = client.get_measurements('Weight', thisweek, lastweek)
   weight
   # >> OrderedDict([(datetime.date(2015, 5, 11), 171.6), (datetime.date(2015, 5, 10), 172.4), (datetime.date(2015, 5,9), 170.2),
   #                 (datetime.date(2015, 5, 8), 171.0),  (datetime.date(2015, 5, 7), 171.2),  (datetime.date(2015, 5, 6), 170.8),
   #                 (datetime.date(2015, 5, 5), 171.8),  (datetime.date(2015, 5, 4), 174.2)])

Measurements are returned as ordered dictionaries. The first argument
specifies the measurement name, which can be any name listed in the
MyFitnessPal
`Check-In <http://www.myfitnesspal.com/measurements/check_in/>`__ page.
When specifying a date range, the order of the date arguments does not
matter.
