Contributing
============

I think I've found a bug
------------------------

We'd love to hear about it -- create a bug report `on github <https://github.com/coddingtonbear/python-myfitnesspal/issues>`_ and be sure to include:

- A description of what you were doing when the error occurred.  Were you trying to fetch your diary, exercises, or measurements?  Were you trying to look up food?  The more we know about what you were doing, the easier ti will be to find the problem.
- A traceback, if at all possible.  Without a traceback, it's really hard to know what kind of problem you're running into, and given that a lot of what this library does is interact with individuals' accounts, reproducing the bug might not be possible, and a traceback will at least give hints about what's going wrong.

I want to add a new feature
---------------------------

You're a hero.  New feature submissions are almost always welcome, but we recommend `starting a discussion <https://github.com/coddingtonbear/python-myfitnesspal/discussions>`_ to make sure that this feature isn't already under development by somebody else, and to possibly talk through how you're planning to implement a feature to make sure it'll sail through the Pull Request Review process as smoothly as possible.

There are a few things to keep in mind for your submission in order to help it sail through the review process smoothly including:

- The build process will most likely inform you if you've missed something, but your submission should follow the project's style and standards including:

  - Proper typings for your methods and variables.
  - Following of the standard ``black`` style.

- Your Pull Request description should include a clear description of what problem your submission solves and why.
- Your submission should include a little documentation if at all possible including:

  - API Documentation covering your newly-added public methods and properties.  This is mostly automated, luckily; just make sure you've added a docstring and proper types to your methods.
  - Maybe a "How to" article in the docs to show folks how to use the feature your new submission adds.

- If you want extra credit, some tests.  We recognize that this is mostly an integration tool, and that testing such things is extremely tricky, but if you can think of a way of making your work testable, we'd all appreciate it.

Once you've developed your feature, post a Pull Request, and the community and collaborators will have a look at what you've put together and possibly post comments and/or suggestions for your consideration.  You need at least one official maintainer's approval before the Pull Request can be merged into the codebase.

I have a feature idea
---------------------

Start a `discussion <https://github.com/coddingtonbear/python-myfitnesspal/discussions>`_ about it.  Maybe you can find somebody to help you bring it to fruition.
