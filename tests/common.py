from contextlib import contextmanager

from wtforms.validators import StopValidation
from wtforms.validators import ValidationError


class DummyTranslations:
    def gettext(self, string):
        return string

    def ngettext(self, singular, plural, n):
        if n == 1:
            return singular

        return plural


class DummyField:
    _translations = DummyTranslations()

    def __init__(self, data, errors=(), raw_data=None):
        self.data = data
        self.errors = list(errors)
        self.raw_data = raw_data

    def gettext(self, string):
        return self._translations.gettext(string)

    def ngettext(self, singular, plural, n):
        return self._translations.ngettext(singular, plural, n)


def grab_error_message(callable, form, field):
    try:
        callable(form, field)
    except ValidationError as e:
        return e.args[0]


def grab_stop_message(callable, form, field):
    try:
        callable(form, field)
    except StopValidation as e:
        return e.args[0]


def contains_validator(field, v_type):
    for v in field.validators:
        if isinstance(v, v_type):
            return True
    return False


class DummyPostData(dict):
    def getlist(self, key):
        v = self[key]
        if not isinstance(v, (list, tuple)):
            v = [v]
        return v


@contextmanager
def assert_raises_text(e_type, text):
    import re

    try:
        yield
    except e_type as e:
        if not re.match(text, e.args[0]):
            raise AssertionError(
                f"Exception raised: {e!r} but text {e.args[0]!r} "
                f"did not match pattern {text!r}"
            ) from e
    else:
        raise AssertionError(f"Expected Exception {e_type!r}, did not get it")
