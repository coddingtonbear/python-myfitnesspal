# 2.0.0 (2022-08-26)

* Now uses the [`browser_cookie3`](https://github.com/borisbabic/browser_cookie3) library for gathering log in credentials instead of logging in to MyFitnessPal directly.  This became necessary due to the recent addition of a hidden captcha in the log-in flow for MyFitnessPal; see [Issue #144](https://github.com/coddingtonbear/python-myfitnesspal/issues/144) for details.

# 1.13 (2018-11-20)

* Adds support for searching for food items and accessing their nutritional values.  Thanks @pydolan!

# 1.12 (2018-09-16)

* Adds support for accessing exercise information via the '.exercise' property.  Thanks @cathyyul!
* Adds functionality allowing one to set measurements; thanks @rbelzile!
* Adds 'completion' property to indicate whether an entry was marked completed.  Thanks @samhinshaw!
* Fixes support for fetching exercise names from public profiles.  Thanks again, @samhinshaw!
* Fixes a bug introduced by MFP UI changes causing get_goals to stop working properly.  Thanks for the fix, @zagi!
* Fixes a bug that would cause loading data to fail if no completion div existed.  Thanks @datamachine!
* Fixes a bug that caused 'n/a' appearing in a column to cause data to be unfetchable.  Thanks @jgissend10!

Note that version 1.11 does not exist; I'm just not very good at using a computer.

# 1.10 (2017-08-29)

* Adds support for fetching exercise information.  Thanks @samhinshaw!

# 1.9 (2017-06-15)

* Adds support for fetching `unit`, `quantity`, and `short_name` for entries.

# 1.8 (2016-01-27)

* Refactoring to support username differences related to logging-in to
  MFP via Facebook.

# 1.7.1 (2016-01-24)

* Fixes bug in measurement iteration on Python 3 (Thanks @dchristle!).
* Moves ``demo.py`` into command-line subcommand named ``day`` with some alterations.

# 1.7 (2016-01-24)

* Adds command-line API.  Currently only two commands have been added: ``store-password`` and ``delete-password``.
* Adds keyring support.  The application will now fetch passwords from the system keyring if they are unspecified.  You can store passwords in the keychain usin g the new ``store-password`` subcommand.

# 1.6 (2015-07-11)

* Adds Python 3 support and drops support for Python 2.6.

# 1.5 (2015-05-15)

* Adds new `get_measurements` method which returns measurements entered into MyFitnessPal.

# 1.4 (2015-03-24)

* Adds support for fetching one's water consumption and notes.

# 1.3 (2014-10-24)

* Connects to MyFitnessPal using a secure connection (https) rather than http.
* Properly alerts you in situations in which you've entered an incorrect username and/or password.
* Allows you to view diaries of users other than the logged-in user.

# 1.2 (2013-08-03)

* Simplifies method signature for selecting diary entries by date.

# 1.1 (2013-07-30)

* Adds unit awareness (optionally -- by using the `unit_aware` keyword argument).

# 1.0 (2013-07-20)

* Initial release.
