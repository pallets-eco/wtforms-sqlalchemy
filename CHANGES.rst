Version 0.4.2
-------------

Released on October 25th, 2024

- move the project to pallets-eco organization
- move from `master` branch to `main`
- move to pyproject.toml
- move to src directory
- remove python 3.8 support
- use pre-commit configuration from flask
- python 3.13 support

Version 0.4.1
-------------

Released on January 5th, 2024

-  Allow to override the default blank value. (:pr:`38`)

Version 0.4.0
-------------

Released on January 4th, 2024

-  Stop support for python 3.6 and 3.7. Start support for python3
   3.11 and 3.12. (:pr:`41`)
-  ``render_kw`` support (:pr:`42`)
-  ``optgroup`` support (:pr:`44`)
-  SQLAlchemy 2.0 support (:pr:`45`)

Version 0.3
-----------

Released on November 6th, 2021

-  Wtforms 3 support. (:pr:`35`)
-  SQLAlchemy 1.4 tests fixes. (:pr:`34`)
-  Switched from Travis CI to Github Actions (:pr:`33`)
-  Abandon deperecated validator. (:pr:`32`)

Version 0.2
-----------

Released on June 21st, 2020

-   Auto-generated ``DecimalField`` does not limit places for ``Float``
    columns. (:pr:`2`)
-   Add an example of using this library with Flask-SQAlchemy. (:pr:`3`)
-   Generating a form from a model copies any lists of validators
    passed in ``field_args`` to prevent modifying a shared value across
    forms. (:pr:`5`)
-   Don't add a ``Length`` validator when the column's length is not an
    int. (:pr:`6`)
-   Add ``QueryRadioField``, like ``QuerySelectField`` except
    it renders a list of radio fields. Add ``QueryCheckboxField``, like
    ``QuerySelectMultipleField`` except it renders a list of checkbox
    fields. (:pr:`8`)
-   Fix a compatibility issue with SQLAlchemy 2.1 that caused
    ``QuerySelectField`` to fail with a ``ValueError``. (:issue:`9`, :pr:`10`,
    :pr:`11`)
-   QuerySelectField.query allowing no results instead of falling back to
    ``query_factory``. (:pr:`15`)
-   Explicitly check if db_session is None in converter. (:pr:`17`)
-   Check for ``sqlalchemy.`` to avoid matching packages with names starting
    with ``sqlalchemy`` (6237a0f_)
-   Use SQLAlchemy's Column.doc for WTForm's Field.description (:pr:`21`)
-   Stopped support for python < 3.5 and added a style pre-commit hook. (:pr:`23`)
-   Documentation cleanup. (:pr:`24`)

.. _6237a0f: https://github.com/wtforms/wtforms-sqlalchemy/commit/6237a0f9e53ec5f22048be7f129e29f7f1c58448

Version 0.1
-----------

Released on January 18th, 2015

-   Initial release, extracted from WTForms 2.1.
