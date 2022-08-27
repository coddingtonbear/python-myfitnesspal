Upgrading from 1.x to 2.x
=========================

Between the 1.x and 2.x versions of this library,
the mechanism used for authentication changed,
and this change has an impact
on how you instantiate the ``myfitnesspal.Client`` object.

For more information about why this change was necessary,
see `Issue #144 <https://github.com/coddingtonbear/python-myfitnesspal/issues/144>`_.

Version 1.x (Obsolete)
----------------------

Before getting started,
you would store a password in your system keyring
for the user account you would like to use
(in this example: 'myusername').

In your code, you would then instantiate your
``myfitnespal.Client`` like this:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client('myusername')

Version 2.x (Current)
---------------------

Before getting started,
now you should open a web browser on the same computer
you will be using this library from,
go to `https://myfitnesspal.com/ <https://myfitnesspal.com/>`_,
and log in to MyFitnessPal using
the user account you would like to use.

In your code, you can then instantiate your
``myfitnespal.Client`` like this:

.. code:: python

   import myfitnesspal

   client = myfitnesspal.Client()

Note that the instantiation no longer accepts a username,
and instead reads the log in information directly
from your browser.
