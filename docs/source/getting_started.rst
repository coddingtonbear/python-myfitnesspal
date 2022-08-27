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

This library uses your local browser's MyFitnessPal cookies
for interacting with MyFitnessPal via the `browser_cookie3 <https://github.com/borisbabic/browser_cookie3>`_ library. 
To control which user account this library uses for interacting with MyFitnessPal,
just log in to the appropriate account in your browser
and,
with a bit of luck,
python-myfitnesspal should be able to find the authentication credentials needed.

By default, this library will look for cookies set for the ``www.myfitnesspal.com`` and ``myfitnesspal.com`` domains in all browsers supported by ``browser_cookie3``.  You can control which cookiejar is used by passing a ``http.cookiejar.CookieJar`` object via the constructor's `cookiejar` keyword parameter.  See `browser_cookie3's readme <https://github.com/borisbabic/browser_cookie3>`_ for details around how you might select a cookiejar from a particular browser.

.. note::

   Starting on August 25th, 2022, MyFitnessPal added
   a hidden captcha to their login flow.
   That change unfortunately prevents this library from logging-in directly,
   and as of version 2.0 of python-myfitnesspal,
   this library now relies on reading browser cookies directly
   for gathering login credentials.

   See `Issue #144 <https://github.com/coddingtonbear/python-myfitnesspal/issues/144>`_ for details and context.
