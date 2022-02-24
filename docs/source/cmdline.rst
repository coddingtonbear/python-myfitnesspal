Using the Command-Line API
==========================

Although most people will probably be using Python-MyFitnessPal as a way
of integrating their MyFitnessPal data into another application,
Python-MyFitnessPal does provide a command-line API with a handful of
commands described below.

``store-password $USERNAME``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Store a password for a given MyFitnessPal account in your system’s
keyring.

``delete-password $USERNAME``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Delete a password for a given MyFitnessPal account from your system
keyring.

``day $USERNAME [$DATE]``
~~~~~~~~~~~~~~~~~~~~~~~~~

Display meals and totals for a given date. If no date is specified,
totals will be printed for today.
