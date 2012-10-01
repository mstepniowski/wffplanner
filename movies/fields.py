import base64
import zlib

import json

from django import forms
from django.forms import widgets
from django.db import models
from django.core import exceptions
from django.core.serializers.json import DjangoJSONEncoder


class JSONTextareaWidget(widgets.Textarea):
    def render(self, name, value, attrs=None):
        if isinstance(value, basestring):
            # value seems to be already encoded
            return super(JSONTextareaWidget, self).render(name, value, attrs)
        try:
            value = json.dumps(value, cls=DjangoJSONEncoder, sort_keys=True)
            return super(JSONTextareaWidget, self).render(name, value, attrs)
        except TypeError, e:
            raise ValueError(e)


class JSONFormField(forms.CharField):
    widget = JSONTextareaWidget

    def __init__(self, *args, **kwargs):
        self.json_type = kwargs.pop('json_type', None)
        super(JSONFormField, self).__init__(*args, **kwargs)

    def clean(self, value):
        value = super(JSONFormField, self).clean(value)
        try:
            json_value = json.loads(value)
            if self.json_type is not None and not isinstance(json_value, self.json_type):
                raise forms.ValidationError('JSON object is not of type %s' % self.json_type)
            return value
        except ValueError, e:
            raise forms.ValidationError('Enter a valid JSON value. Error: %s' % e)


class JSONField(models.TextField):
    """JSONField is a generic textfield that neatly serializes/unserializes
    JSON objects seamlessly"""
    # Used so to_python() is called
    __metaclass__ = models.SubfieldBase
    # Minimum length of value before compression kicks in
    compression_threshold = 64

    def __init__(self, verbose_name=None, json_type=None, compress=False, *args, **kwargs):
        self.json_type = json_type
        self.compress = compress
        super(JSONField, self).__init__(verbose_name, *args, **kwargs)

    # An accesor used only in South introspection,
    # which stupidly calls any callable it receives
    # and then runs repr on it!
    def get_json_type(self):
        class Repr:
            """A class that always returns the __repr__ it's told to."""
            def __init__(self, repr):
                self.repr = repr
            def __repr__(self):
                return self.repr

        if self.json_type is None:
            return None
        else:
            return Repr(self.json_type.__name__)

    def to_python(self, value):
        """Convert our string value to JSON after we load it from the DB"""

        if isinstance(value, basestring):
            if self.compress and value.startswith('zlib;;'):
                value = zlib.decompress(base64.decodestring(value[6:]))

            try:
                value = json.loads(value)
            except ValueError:
                pass

        if self.json_type and not isinstance(value, self.json_type):
            raise exceptions.ValidationError(
                "%r is not of type %s (error occured when trying to access "
                "'%s.%s' field)" %
                (value, self.json_type, self.model._meta.db_table, self.name))
        return value

    def get_db_prep_save(self, value, connection):
        """Convert our JSON object to a string before we save"""

        if self.json_type and not isinstance(value, self.json_type):
            raise TypeError("%r is not of type %s" % (value, self.json_type))

        try:
            value = json.dumps(value)
        except TypeError, e:
            raise ValueError(e)

        if self.compress and len(value) >= self.compression_threshold:
            value = 'zlib;;' + base64.encodestring(zlib.compress(value))

        return super(JSONField, self).get_db_prep_save(value, connection=connection)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

    def formfield(self, **kwargs):
        defaults = {'form_class': JSONFormField, 'json_type': self.json_type}
        defaults.update(kwargs)
        return super(JSONField, self).formfield(**defaults)


try:
    from south.modelsinspector import add_introspection_rules
except ImportError:
    pass
else:
    add_introspection_rules([(
        [JSONField],
        [],
        {
            'json_type': ['get_json_type', {'default': None}],
            'compress': ['compress', {'default': False}],
        },
    )], ["^movies\.fields\.JSONField"])
