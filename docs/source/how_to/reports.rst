Accessing Reports
=================

To access report data from the past 30 days:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   client.get_report(report_name="Net Calories", report_category="Nutrition")
   # >> OrderedDict([(datetime.date(2015, 5, 14), 1701.0), (datetime.date(2015, 5, 13), 1732.8), (datetime.date(2015, 5,12), 1721.8),
   #                 (datetime.date(2015, 5, 11), 1701.6), (datetime.date(2015, 5, 10), 1272.4), (datetime.date(2015, 5, 9), 1720.2),
   #                 (datetime.date(2015, 5, 8), 1071.0),  (datetime.date(2015, 5, 7), 1721.2),  (datetime.date(2015, 5, 6), 1270.8),
   #                 (datetime.date(2015, 5, 5), 1701.8),  (datetime.date(2015, 5, 4), 1724.2),  (datetime.date(2015, 5, 3), 1722.2),
   #                 (datetime.date(2015, 5, 2), 1701.0),  (datetime.date(2015, 5, 1), 1721.2),  (datetime.date(2015, 4, 30), 1721.6),
   #                 (datetime.date(2015, 4, 29), 1072.4), (datetime.date(2015, 4, 28), 1272.2), (datetime.date(2015, 4, 27), 1723.2),
   #                 (datetime.date(2015, 4, 26), 1791.8), (datetime.date(2015, 4, 25), 1720.8), (datetime.date(2015, 4, 24), 1721.2),
   #                 (datetime.date(2015, 4, 23), 1721.6), (datetime.date(2015, 4, 22), 1723.2), (datetime.date(2015, 4, 21), 1724.2),
   #                 (datetime.date(2015, 4, 20), 1273.6), (datetime.date(2015, 4, 19), 1721.8), (datetime.date(2015, 4, 18), 1720.4),
   #                 (datetime.date(2015, 4, 17), 1629.8), (datetime.date(2015, 4, 16), 1270.4), (datetime.date(2015, 4, 15), 1270.8),
   #                 (datetime.date(2015, 4, 14), 1721.6)])

.. code:: python

   import datetime

   may = datetime.date(2015, 5, 1)

   client.get_report("Net Calories", "Nutrition", may)
   # >> OrderedDict([(datetime.date(2015, 5, 14), 172.8), (datetime.date(2015, 5, 13), 173.1), (datetime.date(2015, 5, 12), 127.7),
   #                 (datetime.date(2015, 5, 11), 172.7), (datetime.date(2015, 5, 10), 172.8), (datetime.date(2015, 5, 9), 172.4),
   #                 (datetime.date(2015, 5, 8), 172.6),  (datetime.date(2015, 5, 7), 172.7),  (datetime.date(2015, 5, 6), 172.6),
   #                 (datetime.date(2015, 5, 5), 172.9),  (datetime.date(2015, 5, 4), 173.0),  (datetime.date(2015, 5, 3), 172.6),
   #                 (datetime.date(2015, 5, 2), 172.6),  (datetime.date(2015, 5, 1), 172.7)])

To access report data within a date range:

.. code:: python

   thisweek = datetime.date(2015, 5, 11)
   lastweek = datetime.date(2015, 5, 4)

   client.get_report("Net Calories", "Nutrition", thisweek, lastweek)
   # >> OrderedDict([(datetime.date(2015, 5, 11), 1721.6), (datetime.date(2015, 5, 10), 1722.4), (datetime.date(2015, 5,9), 1720.2),
   #                 (datetime.date(2015, 5, 8), 1271.0),  (datetime.date(2015, 5, 7), 1721.2),  (datetime.date(2015, 5, 6), 1720.8),
   #                 (datetime.date(2015, 5, 5), 1721.8),  (datetime.date(2015, 5, 4), 1274.2)])

Report data is returned as ordered dictionaries. The first argument specifies the report name, the second argument specifies the category name - both of which can be anything listed in the MyFitnessPal `Reports <https://www.myfitnesspal.com/reports>`_ page. When specifying a date range, the order of the date arguments does not matter.
