Searching for Foods
-------------------

To search for items:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   food_items = client.get_food_search_results("bacon cheeseburger")
   food_items
   # >> [<Bacon Cheeseburger -- Sodexo Campus>,
   # <Junior Bacon Cheeseburger -- Wendy's>,
   # <Bacon Cheeseburger -- Continental Café>,
   # <Bacon Cheddar Cheeseburger -- Applebees>,
   # <Bacon Cheeseburger - Plain -- Homemade>,
   # <Jr. Bacon Cheeseburger -- Wendys>,
   # ...

   print("{} ({}), {}, cals={}, mfp_id={}".format(
       food_items[0].name,
       food_items[0].brand,
       food_items[0].serving,
       food_items[0].calories,
       food_items[0].mfp_id
   ))
   # > Bacon Cheeseburger (Sodexo Campus), 1 Sandwich, cals = 420.0

To get details for a particular food:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

   item = client.get_food_item_details("89755756637885")
   item.servings
   # > [<1.00 x Sandwich>]
   item.saturated_fat
   # > 10.0
