Getting Started
===============

Installation
------------

You can either install from pip::

  pip install myfitnesspal

*or* checkout and install the source from the `github repository <https://github.com/coddingtonbear/python-myfitnesspal>`_::

  git clone https://github.com/coddingtonbear/python-myfitnesspal.git
  cd python-myfitnesspal
  python setup.py install


Authentication
--------------

It is a good security practice to not type out the passwords for any of your services (including MyFitnessPal) in either a source file or in the console in such a way that somebody else might be able to read them.  Toward that end, python-myfitnesspal allows you to use your system keyring.

To store your MyFitnessPal password in the system keyring, run::

  myfitnesspal store-password my_username

You will immediately be asked for your password, and that password will be stored in your system keyring for later interactions with MyFitnessPal.

Please note that all examples below *assume* you've stored your password in your system keyring like above, but you can also provide your password by providing your password as a keyword argument to the `myfitnesspal.Client` instance:

.. code:: python

   client = myfitnesspal.Client('my_username', password='my_password')
