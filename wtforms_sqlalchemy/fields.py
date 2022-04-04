"""
Useful form fields for use with SQLAlchemy ORM.
"""
import operator
import itertools

from wtforms import widgets
from wtforms.fields import FieldList, SelectFieldBase
from wtforms.validators import ValidationError
from wtforms.widgets.core import html_params, Markup

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
    "ModelFieldList",
)

DELETE_BUTTON = '_MFLTW_DEL'
ADD_BUTTON = '_MFLTW_ADD'

class _ModelFieldListTableWiget():
    prefix = '_MFLTW-'

    def __init__(self, horizontal_layout, prefix_label=True, with_table_tag=True):
        self.with_table_tag = with_table_tag
        self.prefix_label = prefix_label
        self.horizontal_layout = horizontal_layout


    def build_horizontal_layout(self, field, **kwargs):
        html = []


        if self.with_table_tag:
            kwargs.setdefault("id", field.id)
            html.append("<table %s>" % html_params(**kwargs))
        
        # Add a visible invisible submit button to allow submit by pressing enter
        html.append("""<input type="submit" style="overflow: visible !important; height: 0 !important; width: 0 !important; margin: 0 !important; border: 0 !important; padding: 0 !important; display: block !important;">""")
        
        hidden = ""
        for subfield in field:
            if subfield.type in ("HiddenField", "CSRFTokenField"):
                hidden += str(subfield)
            else:
                html.append("<tr>")
                if self.prefix_label:
                    html.append(f"<td>{subfield.label} {subfield()}</td>")
                else:
                    html.append(f"<td>{subfield()} {subfield.label}</td>")

                delete = self.parent._separator.join([subfield.id, DELETE_BUTTON])
                html.append(f"<td><input type='submit' class='{DELETE_BUTTON}' value='delete' name='{delete}'></td>")

        if self.with_table_tag:
            html.append("</table>")
        if hidden:
            html.append(hidden)

        add = self.parent._separator.join([field.id, ADD_BUTTON])
        html.append(f"<input type='submit' class='{ADD_BUTTON}' value='Add {field.label}' name='{add}'>")
        
        return Markup("".join(html))   


    def build_vertical_layout(self, field, **kwargs):
        html = []

        html.append(f"<div class='{self.prefix}nested-entries-container'>")

        # Add a visible invisible submit button to allow submit by pressing enter
        html.append("""<input type="submit" style="overflow: visible !important; height: 0 !important; width: 0 !important; margin: 0 !important; border: 0 !important; padding: 0 !important; display: block !important;">""")
        
        if self.with_table_tag:
            kwargs.setdefault("id", field.id)
            html.append(f"<table class='{self.prefix}nested-entries' {html_params(**kwargs)}>")

        hidden = ""
        if len(field) == 0:
            html.append(f"<tbody><tr><td>There are no {field.label.text.lower()}</td><tr></tbody>")
        else:
            # Build up table head
            html.append("<thead><tr>")
            for subfield in field:
                for subsubfield in subfield:
                    html.append(f"<th class='{subsubfield.id}'>{subsubfield.label}</th>")
                break
            html.append(f"<th class='{self.prefix}actions'>-</th>")
            html.append("</tr></thead>")

            # Build up table body
            html.append("<tbody>")

            for subfield in field:
                if subfield.type in ("HiddenField", "CSRFTokenField"):
                    hidden += str(subfield)
                else:
                    html.append("<tr>")
                    for subsubfield in subfield:
                        html.append(f"<td>{subsubfield()}</td>")
                    delete = field._separator.join([subfield.id, DELETE_BUTTON])
                    html.append(f"<td><button class='{DELETE_BUTTON}' name='{delete}'>Delete</button></td>")    
                    html.append("</tr>")
            
            html.append("</tbody>")

        if self.with_table_tag:
            html.append("</table>")
        if hidden:
            html.append(hidden)

        add = field._separator.join([field.id, ADD_BUTTON])
        html.append(f"<button class='{ADD_BUTTON}' name='{add}'>Add {field.label.text.lower()}</button>")

        html.append('</div>')

        return Markup("".join(html))  


    def __call__(self, field, **kwargs):
        if self.horizontal_layout:
            return self.build_horizontal_layout(field, **kwargs)
        else:
            return self.build_vertical_layout(field, **kwargs)


class ModelFieldList(FieldList): 
    FROM_DB_ID = "_MFL_PK"
    NEW_ID = "_MFL_NEW"

    def __init__(self, unbound_field, horizontal_layout=False, model=None, *args, **kwargs):
        self.widget = _ModelFieldListTableWiget(horizontal_layout)
        self.model = model

        super().__init__(unbound_field, *args, **kwargs)
        
        if not self.model:
            raise ValueError("ModelFieldList requires model to be set")

    def _rebuild_form(self, formdata):
        db_elements_ids = set()
        db_elements_deleted = set()

        new_elements_indices = set()
        new_elements_deleted = set()

        add_button_pressed = False

        prefix = self.id + self._separator

        # Examine all elements in formdata
        for form_element in formdata:
            if not form_element.startswith(prefix):
                continue

            if form_element[len(prefix):] == ADD_BUTTON:
                # _MFLTW_ADD
                add_button_pressed = True
                self.valid = False
                continue
            
            parts = form_element[len(prefix):].split(self._separator)

            if parts[0] == self.FROM_DB_ID:
                # _MFL_PK-10232
                _id = int(parts[1])
                if len(parts) == 3 and parts[2] == DELETE_BUTTON:
                    # _MFL_PK-10232-_MFLTW_DEL
                    db_elements_deleted.add(_id)
                    self.valid = False
                else:
                    db_elements_ids.add(_id)

            # See if the element was added to the form earlier (without processing in db)
            elif parts[0] == self.NEW_ID:
                # _MFL_NEW-1598
                _id = int(parts[1])
                if len(parts) == 3 and parts[2] == DELETE_BUTTON:
                    # _MFL_NEW-1598-_MFLTW_DEL
                    new_elements_deleted.add(_id)        
                    self.valid = False
                else:
                    new_elements_indices.add(_id)


        # Now, add rows according to results from above loop

        # First, add database form entries if they were not deleted
        for _id, obj in self.object_data.items():
            if _id in db_elements_ids and _id not in db_elements_deleted:
                self._add_entry(formdata=formdata, sql_obj=obj)

        # Then, add new entries if they were not deleted
        for new_ix in sorted(new_elements_indices - new_elements_deleted):
            self._add_entry(formdata=formdata, index=new_ix)

        # Finally, add an empty entry if the add button was pressed
        if add_button_pressed:
            self._add_entry()            
        

    def _add_entry(self, formdata=None, sql_obj=None, index=None):
        assert (
            not self.max_entries or len(self.entries) < self.max_entries
        ), "You cannot have more than max_entries entries in this FieldList"

        if sql_obj:
            entry_type = self.FROM_DB_ID
            entry_id = str(sql_obj.id)
        elif index:
            self.last_index = index
            entry_type = self.NEW_ID
            entry_id = str(index)
        else:
            self.last_index += 1
            entry_type = self.NEW_ID
            entry_id = str(self.last_index)
 
        field_name = self._separator.join([self.short_name, entry_type, entry_id])
        field_id = self._separator.join([self.id, entry_type, entry_id])

        field = self.unbound_field.bind(
            form=None,
            name=field_name,
            prefix=self._prefix,
            id=field_id,
            _meta=self.meta,
            translations=self._translations,
        )

        field.process(formdata, sql_obj)
        self.entries.append(field)

        return field

    def process(self, formdata, data=None, extra_filters=None):
        if extra_filters:
            raise TypeError(
                "FieldList does not accept any filters. Instead, define"
                " them on the enclosed field."
            )
        
        self.valid = True
        self.entries = []
        
        self.object_data = {obj.id: obj for obj in data} if data else {}

        if formdata:
            # Add entries based on formdata
            self._rebuild_form(formdata)

        else:
            # Add entries based on self.object_data
            for obj in self.object_data.values():
                self._add_entry(formdata=None, sql_obj=obj)

        # Add entries until min_entries is reached
        while len(self.entries) < self.min_entries:
            self._add_entry(formdata)

    def validate(self, form, extra_validators=()):
        self.errors = []

        valid = self.valid
        for subfield in self.entries:
            valid = subfield.validate(form) and valid
            self.errors.append(subfield.errors)

        if not any(x for x in self.errors):
            self.errors = []

        chain = itertools.chain(self.validators, extra_validators)
        self._run_validation_chain(form, chain)

        return valid and len(self.errors) == 0

    def populate_obj(self, obj, name):
        relation = getattr(obj, name)

        prefix = self.id + self._separator
        updated = set()

        for entry in self.entries:
            if not entry.id.startswith(prefix):
                continue

            parts = entry.id[len(prefix):].split(self._separator, 2)
            _fake_util = type("_fake", (object,), {})
            
            if parts[0] == self.FROM_DB_ID:
                # _MFL_PK-10232
                _id = int(parts[1])


                # If the object is found in self.object_data, update it.
                if obj := self.object_data.get(_id):
                    fake_obj = _fake_util()
                    fake_obj.data = obj
                    entry.populate_obj(fake_obj, "data")
                    
                    obj = fake_obj.data
                    
                    updated.add(obj.id)

            # If the object was newly added, add it to relation
            elif parts[0] == self.NEW_ID:
                # _MFL_NEW-1598
                fake_obj = _fake_util()
                fake_obj.data = self.model()

                entry.populate_obj(fake_obj, "data")
                
                new_model = fake_obj.data

                relation.append(new_model) 

        # Finally also if relation has any objects that are missing
        #   in self.entries, if so delete them from relation
        for deleted_id in (set(self.object_data.keys()) - updated):
            obj = self.object_data.get(deleted_id)
            try:
                ix = relation.index(obj)
            except ValueError:
                continue
            
            db_obj = relation.pop(ix)


class QuerySelectField(SelectFieldBase):
    """
    Will display a select drop-down field to choose between ORM results in a
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

    If `allow_blank` is set to `True`, then a blank choice will be added to the
    top of the list. Selecting this choice will result in the `data` property
    being `None`. The label for this blank choice can be set by specifying the
    `blank_text` parameter.
    """

    widget = widgets.Select()

    def __init__(
        self,
        label=None,
        validators=None,
        query_factory=None,
        get_pk=None,
        get_label=None,
        allow_blank=False,
        blank_text="",
        **kwargs
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

        self.allow_blank = allow_blank
        self.blank_text = blank_text
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

    def iter_choices(self):
        if self.allow_blank:
            yield ("__None", self.blank_text, self.data is None)

        for pk, obj in self._get_object_list():
            yield (pk, self.get_label(obj), obj == self.data)

    def process_formdata(self, valuelist):
        if valuelist:
            if self.allow_blank and valuelist[0] == "__None":
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
    """
    Very similar to QuerySelectField with the difference that this will
    display a multiple select. The data property will hold a list with ORM
    model instances and will be an empty list when no value is selected.

    If any of the items in the data list or submitted form data cannot be
    found in the query, this will result in a validation error.
    """

    widget = widgets.Select(multiple=True)

    def __init__(self, label=None, validators=None, default=None, **kwargs):
        if default is None:
            default = []
        super().__init__(label, validators, default=default, **kwargs)
        if kwargs.get("allow_blank", False):
            import warnings

            warnings.warn(
                "allow_blank=True does not do anything for QuerySelectMultipleField."
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
            yield (pk, self.get_label(obj), obj in self.data)

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
