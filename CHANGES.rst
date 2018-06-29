WTForms-SQLAlchemy Changelog
============================

Version 0.2
-----------

Unreleased

-   Fix a compatibility issue with SQLAlchemy 2.1 that caused
    :class:`~ext.sqlalchemy.fields.QuerySelectField` to fail with
    ``ValueError: too many values to unpack``. (`#9`_, `#10`_, `#11`_)

.. _#9: https://github.com/wtforms/wtforms-sqlalchemy/issues/9
.. _#10: https://github.com/wtforms/wtforms-sqlalchemy/pull/10
.. _#11: https://github.com/wtforms/wtforms-sqlalchemy/pull/11



Version 0.1
-----------

Released on January 18th, 2015

-   Initial release, extracted from WTForms 2.1.
