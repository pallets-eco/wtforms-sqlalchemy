Changes
=======


Version 0.2
-----------

Unreleased

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

.. _#2: https://github.com/wtforms/wtforms-sqlalchemy/pull/2
.. _#3: https://github.com/wtforms/wtforms-sqlalchemy/pull/3
.. _#5: https://github.com/wtforms/wtforms-sqlalchemy/pull/5
.. _#6: https://github.com/wtforms/wtforms-sqlalchemy/pull/6
.. _#8: https://github.com/wtforms/wtforms-sqlalchemy/pull/8
.. _#9: https://github.com/wtforms/wtforms-sqlalchemy/issues/9
.. _#10: https://github.com/wtforms/wtforms-sqlalchemy/pull/10
.. _#11: https://github.com/wtforms/wtforms-sqlalchemy/pull/11


Version 0.1
-----------

Released on January 18th, 2015

-   Initial release, extracted from WTForms 2.1.
