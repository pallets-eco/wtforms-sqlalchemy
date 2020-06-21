Changes
=======

Version 0.x
-----------

Unreleased

Version 0.2
-----------

Released on June 21st, 2020

-   Auto-generated ``DecimalField`` does not limit places for ``Float``
    columns. (`#2`_)
-   Add an example of using this library with Flask-SQAlchemy. (`#3`_)
-   Generating a form from a model copies any lists of validators
    passed in ``field_args`` to prevent modifying a shared value across
    forms. (`#5`_)
-   Don't add a ``Length`` validator when the column's length is not an
    int. (`#6`_)
-   Add ``QueryRadioField``, like ``QuerySelectField`` except
    it renders a list of radio fields. Add ``QueryCheckboxField``, like
    ``QuerySelectMultipleField`` except it renders a list of checkbox
    fields. (`#8`_)
-   Fix a compatibility issue with SQLAlchemy 2.1 that caused
    ``QuerySelectField`` to fail with a ``ValueError``. (`#9`_, `#10`_,
    `#11`_)
-   QuerySelectField.query allowing no results instead of falling back to
    ``query_factory``. (`#15`_)
-   Explicitly check if db_session is None in converter. (`#17`_)
-   Check for ``sqlalchemy.`` to avoid matching packages with names starting
    with ``sqlalchemy`` (6237a0f_)
-   Use SQLAlchemy's Column.doc for WTForm's Field.description (`#21`_)
-   Stopped support for python < 3.5 and added a style pre-commit hook. (`#23`_)
-   Documentation cleanup. (`#24`_)

.. _#2: https://github.com/wtforms/wtforms-sqlalchemy/pull/2
.. _#3: https://github.com/wtforms/wtforms-sqlalchemy/pull/3
.. _#5: https://github.com/wtforms/wtforms-sqlalchemy/pull/5
.. _#6: https://github.com/wtforms/wtforms-sqlalchemy/pull/6
.. _#8: https://github.com/wtforms/wtforms-sqlalchemy/pull/8
.. _#9: https://github.com/wtforms/wtforms-sqlalchemy/issues/9
.. _#10: https://github.com/wtforms/wtforms-sqlalchemy/pull/10
.. _#11: https://github.com/wtforms/wtforms-sqlalchemy/pull/11
.. _#15: https://github.com/wtforms/wtforms-sqlalchemy/pull/15
.. _#17: https://github.com/wtforms/wtforms-sqlalchemy/pull/17
.. _6237a0f: https://github.com/wtforms/wtforms-sqlalchemy/commit/6237a0f9e53ec5f22048be7f129e29f7f1c58448
.. _#21: https://github.com/wtforms/wtforms-sqlalchemy/pull/21
.. _#23: https://github.com/wtforms/wtforms-sqlalchemy/pull/23
.. _#24: https://github.com/wtforms/wtforms-sqlalchemy/pull/24

Version 0.1
-----------

Released on January 18th, 2015

-   Initial release, extracted from WTForms 2.1.
