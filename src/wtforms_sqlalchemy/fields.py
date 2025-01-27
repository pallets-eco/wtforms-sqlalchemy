"""Useful form fields for use with SQLAlchemy ORM."""

import operator
from collections import defaultdict

from wtforms import widgets
from wtforms.fields import SelectFieldBase
from wtforms.validators import ValidationError

try:
    from sqlalchemy.orm.util import identity_key

    has_identity_key = True
except ImportError:
    has_identity_key = False


__all__ = (
    "QuerySelectField",
    "QuerySelectMultipleField",
    "QueryRadioField",
    "QueryCheckboxField",
)


class QuerySelectField(SelectFieldBase):
    """Will display a select drop-down field to choose between ORM results in a
    sqlalchemy `Query`.  The `data` property actually will store/keep an ORM
    model instance, not the ID. Submitting a choice which is not in the query
    will result in a validation error.

    This field only works for queries on models whose primary key column(s)
    have a consistent string representation. This means it mostly only works
    for those composed of string, unicode, and integer types. For the most
    part, the primary keys will be auto-detected from the model, alternately
    pass a one-argument callable to `get_pk` which can return a unique
    comparable key.

    The `query` property on the field can be set from within a view to assign
    a query per-instance to the field. If the property is not set, the
    `query_factory` callable passed to the field constructor will be called to
    obtain a query.

    Specify `get_label` to customize the label associated with each option. If
    a string, this is the name of an attribute on the model object to use as
    the label text. If a one-argument callable, this callable will be passed
    model instance and expected to return the label text. Otherwise, the model
    object's `__str__` will be used.


    Specify `get_group` to allow `option` elements to be grouped into `optgroup`
    sections.  If a string, this is the name of an attribute on the model
    containing the group name.  If a one-argument callable, this callable will
    be passed the model instance and expected to return a group name.  Otherwise,
    the `option` elements will not be grouped.  Note: the result of `get_group`
    will be used as both the grouping key and the display label in the `select`
    options.

    Specify `get_render_kw` to apply HTML attributes to each option. If a
    string, this is the name of an attribute on the model containing a
    dictionary.  If a one-argument callable, this callable will be passed the
    model instance and expected to return a dictionary.  Otherwise, an empty
    dictionary will be used.

    If `allow_blank` is set to `True`, then a blank choice will be added to the
    top of the list. Selecting this choice will result in the `data` property
    being `None`. The label for this blank choice can be set by specifying the
    `blank_text` parameter. The value for this blank choice can be set by
    specifying the `blank_value` parameter (default: `__None`).
    """

    widget = widgets.Select()

    def __init__(
        self,
        label=None,
        validators=None,
        query_factory=None,
        get_pk=None,
        get_label=None,
        get_group=None,
        get_render_kw=None,
        allow_blank=False,
        blank_text="",
        blank_value="__None",
        **kwargs,
    ):
        super().__init__(label, validators, **kwargs)
        self.query_factory = query_factory

        if get_pk is None:
            if not has_identity_key:
                raise Exception(
                    "The sqlalchemy identity_key function could not be imported."
                )
            self.get_pk = get_pk_from_identity
        else:
            self.get_pk = get_pk

        if get_label is None:
            self.get_label = lambda x: x
        elif isinstance(get_label, str):
            self.get_label = operator.attrgetter(get_label)
        else:
            self.get_label = get_label

        if get_group is None:
            self._has_groups = False
        else:
            self._has_groups = True
            if isinstance(get_group, str):
                self.get_group = operator.attrgetter(get_group)
            else:
                self.get_group = get_group

        if get_render_kw is None:
            self.get_render_kw = lambda _: {}
        elif isinstance(get_render_kw, str):
            self.get_render_kw = operator.attrgetter(get_render_kw)
        else:
            self.get_render_kw = get_render_kw

        self.allow_blank = allow_blank
        self.blank_text = blank_text
        self.blank_value = blank_value
        self.query = None
        self._object_list = None

    def _get_data(self):
        if self._formdata is not None:
            for pk, obj in self._get_object_list():
                if pk == self._formdata:
                    self._set_data(obj)
                    break
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def _get_object_list(self):
        if self._object_list is None:
            query = self.query if self.query is not None else self.query_factory()
            get_pk = self.get_pk
            self._object_list = list((str(get_pk(obj)), obj) for obj in query)
        return self._object_list

    def _get_blank_choice(self):
        return (self.blank_value, self.blank_text, self.data is None, {})

    def iter_choices(self):
        if self.allow_blank:
            yield self._get_blank_choice()

        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), obj == self.data, self.get_render_kw(obj))

    def has_groups(self):
        return self._has_groups

    def iter_groups(self):
        if self.has_groups():
            if self.allow_blank:
                yield (None, [self._get_blank_choice()])

            groups = defaultdict(list)
            for pk, obj in self._get_object_list():
                groups[self.get_group(obj)].append((pk, obj))
            for group, choices in groups.items():
                yield (group, self._choices_generator(choices))

    def _choices_generator(self, choices):
        if not choices:
            _choices = []
        else:
            _choices = choices

        for pk, obj in _choices:
            yield (pk, self.get_label(obj), obj == self.data, self.get_render_kw(obj))

    def process_formdata(self, valuelist):
        if valuelist:
            if self.allow_blank and valuelist[0] == self.blank_value:
                self.data = None
            else:
                self._data = None
                self._formdata = valuelist[0]

    def pre_validate(self, form):
        data = self.data
        if data is not None:
            for _, obj in self._get_object_list():
                if data == obj:
                    break
            else:
                raise ValidationError(self.gettext("Not a valid choice"))
        elif self._formdata or not self.allow_blank:
            raise ValidationError(self.gettext("Not a valid choice"))


class QuerySelectMultipleField(QuerySelectField):
    """Very similar to QuerySelectField with the difference that this will
    display a multiple select. The data property will hold a list with ORM
    model instances and will be an empty list when no value is selected.

    If any of the items in the data list or submitted form data cannot
    be found in the query, this will result in a validation error.
    """

    widget = widgets.Select(multiple=True)

    def __init__(self, label=None, validators=None, default=None, **kwargs):
        if default is None:
            default = []
        super().__init__(label, validators, default=default, **kwargs)
        if kwargs.get("allow_blank", False):
            import warnings

            warnings.warn(
                "allow_blank=True does not do anything for QuerySelectMultipleField.",
                stacklevel=2,
            )
        self._invalid_formdata = False

    def _get_data(self):
        formdata = self._formdata
        if formdata is not None:
            data = []
            for pk, obj in self._get_object_list():
                if not formdata:
                    break
                elif pk in formdata:
                    formdata.remove(pk)
                    data.append(obj)
            if formdata:
                self._invalid_formdata = True
            self._set_data(data)
        return self._data

    def _set_data(self, data):
        self._data = data
        self._formdata = None

    data = property(_get_data, _set_data)

    def iter_choices(self):
        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), obj in self.data, self.get_render_kw(obj))

    def process_formdata(self, valuelist):
        self._formdata = set(valuelist)

    def pre_validate(self, form):
        if self._invalid_formdata:
            raise ValidationError(self.gettext("Not a valid choice"))
        elif self.data:
            obj_list = list(x[1] for x in self._get_object_list())
            for v in self.data:
                if v not in obj_list:
                    raise ValidationError(self.gettext("Not a valid choice"))


class QueryRadioField(QuerySelectField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.RadioInput()


class QueryCheckboxField(QuerySelectMultipleField):
    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


def get_pk_from_identity(obj):
    key = identity_key(instance=obj)[1]
    return ":".join(str(x) for x in key)
