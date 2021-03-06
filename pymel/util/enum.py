# -*- coding: utf-8 -*-

# enum.py
# Part of enum, a package providing enumerated types for Python.
#
# Copyright © 2007 Ben Finney
# This is free software; you may copy, modify and/or distribute this work
# under the terms of the GNU General Public License, version 2 or later
# or, at your option, the terms of the Python license.

"""Robust enumerated type support in Python

This package provides a module for robust enumerations in Python.

An enumeration object is created with a sequence of string arguments
to the Enum() constructor:

    >>> from enum import Enum
    >>> Colours = Enum('Colours', ['red', 'blue', 'green'])
    >>> Weekdays = Enum('Weekdays', ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'])

The return value is an immutable sequence object with a value for each
of the string arguments. Each value is also available as an attribute
named from the corresponding string argument:

    >>> pizza_night = Weekdays[4]
    >>> shirt_colour = Colours.green

The values are constants that can be compared with values from
the same enumeration, as well as with integers or strings; comparison with other
values will invoke Python's fallback comparisons:

    >>> pizza_night == Weekdays.fri
    True
    >>> shirt_colour > Colours.red
    True
    >>> shirt_colour == "green"
    True

Each value from an enumeration exports its sequence index
as an integer, and can be coerced to a simple string matching the
original arguments used to create the enumeration:

    >>> str(pizza_night)
    'fri'
    >>> shirt_colour.index
    2
"""

__author_name__ = "Ben Finney"
__author_email__ = "ben+python@benfinney.id.au"
#__author__ = "%s <%s>" % (__author_name__, __author_email__) # confuses epydoc
__date__ = "2007-01-24"
__copyright__ = "Copyright © %s %s" % (
    __date__.split('-')[0], __author_name__
)
__license__ = "Choice of GPL or Python license"
__url__ = "http://cheeseshop.python.org/pypi/enum/"
__version__ = "0.4.3"

import operator

class EnumException(Exception):
    """ Base class for all exceptions in this module """
    def __init__(self):
        if self.__class__ is EnumException:
            raise NotImplementedError, \
                "%s is an abstract class for subclassing" % self.__class__

class EnumEmptyError(AssertionError, EnumException):
    """ Raised when attempting to create an empty enumeration """

    def __str__(self):
        return "Enumerations cannot be empty"

class EnumBadKeyError(TypeError, EnumException):
    """ Raised when creating an Enum with non-string keys """

    def __init__(self, key):
        self.key = key

    def __str__(self):
        return "Enumeration keys must be strings: %s" % (self.key,)

class EnumImmutableError(TypeError, EnumException):
    """ Raised when attempting to modify an Enum """

    def __init__(self, *args):
        self.args = args

    def __str__(self):
        return "Enumeration does not allow modification"

class EnumValue(object):
    """ A specific value of an enumerated type """

    def __init__(self, enumtype, index, key, doc=None):
        """ Set up a new instance """
        self.__enumtype = enumtype
        self.__index = index
        self.__key = key
        self.__doc = doc

    def __get_enumtype(self):
        return self.__enumtype
    enumtype = property(__get_enumtype)

    def __get_key(self):
        return self.__key
    key = property(__get_key)

    def __str__(self):
        return "%s" % (self.key)
    def __int__(self):
        return self.index

    def __get_index(self):
        return self.__index
    index = property(__get_index)

    def __repr__(self):
        if self.__doc:
            return "EnumValue(%r, %r, %r, %r, %r)" % (
                self.__enumtype._name,
                self.__index,
                self.__key,
                self.__doc,
            )
        else:
            return "EnumValue(%r, %r, %r)" % (
                self.__enumtype._name,
                self.__index,
                self.__key,
            )


    def __hash__(self):
        return hash(self.__index)

#    def __cmp__(self, other):
#        result = NotImplemented
#        self_type = self.enumtype
#        try:
#            assert self_type == other.enumtype
#            result = cmp(self.index, other.index)
#        except (AssertionError, AttributeError):
#            result = NotImplemented
#
#        return result

    def __cmp__(self, other):
        result = NotImplemented
        self_type = self.enumtype
        try:
            assert self_type == other.enumtype
            result = cmp(self.index, other.index)
        except (AssertionError, AttributeError):
            if isinstance(other, basestring):
                result=cmp(self.key, other)
            elif isinstance(other, int):
                result=cmp(self.index, other)
            else:
                result = NotImplemented

        return result


class Enum(object):
    """ Enumerated type """

    def __init__(self, name, keys, **kwargs):
        """ Create an enumeration instance """

        if not keys:
            raise EnumEmptyError()

        if operator.isMappingType(keys):
            reverse = dict( [ (v,k) for k,v in keys.items() ] )
            keygen = [ ( v, reverse[v]) for v in sorted(reverse.keys()) ]
            values = {}
        else:
            keygen = enumerate( keys )
            values = [None] * len(keys)

        value_type= kwargs.get('value_type', EnumValue)
        #keys = tuple(keys)

        docs = {}
        keyDict = {}
        for val, key in keygen:
            #print val, key
            kwargs = {}
            if isinstance(key, tuple) or isinstance(key, list) and len(key)==2:
                key, doc = key
                docs[val]=doc
                kwargs['doc'] = doc
            value = value_type(self, val, key, **kwargs)
            values[val] = value
            keyDict[key] = val
            try:
                super(Enum, self).__setattr__(key, value)
            except TypeError, e:
                raise EnumBadKeyError(key)

        super(Enum, self).__setattr__('_keys', keyDict)
        super(Enum, self).__setattr__('_values', values)
        super(Enum, self).__setattr__('_docs', docs)
        super(Enum, self).__setattr__('_name', name)

    def __repr__(self):
        return '%s(\n%s)' % (self.__class__.__name__, ',\n'.join([ repr(v) for v in self.values()]))

    def __str__(self):
        return '%s%s' % (self.__class__.__name__, self.keys())

    def __setattr__(self, name, value):
        raise EnumImmutableError(name)

    def __delattr__(self, name):
        raise EnumImmutableError(name)

    def __len__(self):
        return len(self._values)

    def __getitem__(self, index):
        return self._values[index]

    def __setitem__(self, index, value):
        raise EnumImmutableError(index)

    def __delitem__(self, index):
        raise EnumImmutableError(index)

    def __iter__(self):
        return iter(self._values)

    def __contains__(self, value):
        is_member = False
        if isinstance(value, basestring):
            is_member = (value in self._keys)
        else:
            try:
                is_member = (value in self._values)
            except EnumValueCompareError, e:
                is_member = False
        return is_member

    def getIndex(self, key):
        """
        get an index value from a key. this method always returns an index. if a valid index is passed instead of a key, the index will
        be returned unchanged.  this is useful when you need an index, but are not certain whether you are starting with a key or an index.

            >>> units = Enum('units', ['invalid', 'inches', 'feet', 'yards', 'miles', 'millimeters', 'centimeters', 'kilometers', 'meters'])
            >>> units.getIndex('inches')
            1
            >>> units.getIndex(3)
            3
            >>> units.getIndex('hectares')
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator key: 'hectares'
            >>> units.getIndex(10)
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator index: 10
        """
        if isinstance(key, int):
            # got a potential index : checking if it's valid
            if key in self._values:
                return key
            else:
                raise ValueError, "invalid enumerator index: %r" % key
        else:
            # got a key: retrieving index
            try:
                return self._keys[str(key)]
            except:
                raise ValueError, "invalid enumerator key: %r" % key

    def getKey(self, index):
        """
        get a key value from an index. this method always returns a key. if a valid key is passed instead of an index, the key will
        be returned unchanged.  this is useful when you need a key, but are not certain whether you are starting with a key or an index.

            >>> units = Enum('units', ['invalid', 'inches', 'feet', 'yards', 'miles', 'millimeters', 'centimeters', 'kilometers', 'meters'])
            >>> units.getKey(2)
            'feet'
            >>> units.getKey('inches')
            'inches'
            >>> units.getKey(10)
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator index: 10
            >>> units.getKey('hectares')
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator key: 'hectares'
        """

        if isinstance(index, int):
            # got an index: retrieving key
            try:
                return self._values[index].key
            except:
                raise ValueError, "invalid enumerator index: %r" % index
        else:
            # got a potential key : checking if it's valid
            if str(index) in self._keys:
                return index
            else:
                raise ValueError, "invalid enumerator key: %r" % index


    def values(self):
        "return a list of `EnumValue`s"
        if operator.isMappingType(self._values):
            return tuple([ self._values[k] for k in sorted(self._values.keys()) ])
        else:
            return self._values

    def keys(self):
        "return a list of keys as strings"
        if operator.isMappingType(self._values):
            return tuple([ self._values[k].key for k in sorted(self._values.keys()) ])
        else:
            return tuple([ v.key for v in self._values ])

import utilitytypes
class EnumDict(utilitytypes.EquivalencePairs):
    """
    This class provides a dictionary type for storing enumerations.  Keys are string labels, while
    values are enumerated integers.

    To instantiate, pass a sequence of string arguments to the EnumDict() constructor:

        >>> from enum import EnumDict
        >>> Colours = EnumDict(['red', 'blue', 'green'])
        >>> Weekdays = EnumDict(['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun'])
        >>> Weekdays
        {'fri': 4, 'mon': 0, 'sat': 5, 'sun': 6, 'thu': 3, 'tue': 1, 'wed': 2}

    Alternately, a dictionary of label-value pairs can be provided:

        >>> Numbers = EnumDict({'one': 1, 'two': 2, 'hundred' : 100, 'thousand' : 1000 } )

    To convert from one representation to another, just use normal dictionary retrieval, it
    works in either direction:

        >>> Weekdays[4]
        'fri'
        >>> Weekdays['fri']
        4

    If you need a particular representation, but don't know what you're starting from ( for
    example, a value that was passed as an argument ) you can use `EnumDict.key` or
    `EnumDict.value`:

        >>> Weekdays.value(3)
        3
        >>> Weekdays.value('thu')
        3
        >>> Weekdays.key(2)
        'wed'
        >>> Weekdays.key('wed')
        'wed'
    """

    def __init__(self, keys, **kwargs):
        """ Create an enumeration instance """

        if not keys:
            raise EnumEmptyError()

        if operator.isMappingType(keys):
            items = keys.items()
            if isinstance(items[0][0],int):
                byKey = dict( (k,v) for v,k in items )
            else:
                byKey = keys
        else:
            byKey = dict( (k,v) for v,k in enumerate( keys ) )
        super(EnumDict,self).__init__(byKey)

#        for key, value in byKey.items():
#            try:
#                super(EnumDict, self).__setattr__(key, value)
#            except TypeError, e:
#                raise EnumBadKeyError(key)
#
#        super(EnumDict, self).__setattr__('_reverse', {})
#        self.update(byKey)
#
#    def __setattr__(self, name, value):
#        raise EnumImmutableError(name)
#
#    def __delattr__(self, name):
#        raise EnumImmutableError(name)
#
#    def __setitem__(self, index, value):
#        raise EnumImmutableError(index)
#
#    def __delitem__(self, index):
#        raise EnumImmutableError(index)

    def __repr__(self):
        return "%s(%s)" % (self.__class__.__name__, super(EnumDict, self).__repr__())

    def value(self, key):
        """
        get an index value from a key. this method always returns an index. if a valid index is passed instead of a key, the index will
        be returned unchanged.  this is useful when you need an index, but are not certain whether you are starting with a key or an index.

            >>> units = EnumDict('units', ['invalid', 'inches', 'feet', 'yards', 'miles', 'millimeters', 'centimeters', 'kilometers', 'meters'])
            >>> units.value('inches')
            1
            >>> units.value(3)
            3
            >>> units.value('hectares')
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator key: 'hectares'
            >>> units.value(10)
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator index: 10
        """
        if isinstance(key, int):
            # got a potential index : checking if it's valid
            if key in self.values():
                return key
            else:
                raise ValueError, "invalid enumerator value: %r" % key
        else:
            # got a key: retrieving index
            try:
                return dict.__getitem__(self, key)
            except KeyError:
                raise ValueError, "invalid enumerator key: %r" % key

    def key(self, index):
        """
        get a key value from an index. this method always returns a key. if a valid key is passed instead of an index, the key will
        be returned unchanged.  this is useful when you need a key, but are not certain whether you are starting with a key or an index.

            >>> units = EnumDict('units', ['invalid', 'inches', 'feet', 'yards', 'miles', 'millimeters', 'centimeters', 'kilometers', 'meters'])
            >>> units.key(2)
            'feet'
            >>> units.key('inches')
            'inches'
            >>> units.key(10)
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator index: 10
            >>> units.key('hectares')
            Traceback (most recent call last):
              ...
            ValueError: invalid enumerator key: 'hectares'
        """

        if isinstance(index, int):
            # got an index: retrieving key
            try:
                return self._reverse[index]
            except KeyError:
                raise ValueError( "invalid enumerator value: %r" % index )
        else:
            # got a potential key : checking if it's valid
            if index in dict.keys(self):
                return index
            else:
                raise ValueError( "invalid enumerator key: %r" % index)


    def values(self):
        "return a list of ordered integer values"
        return sorted(dict.values(self))


    def keys(self):
        "return a list of keys as strings ordered by their enumerator value"
        return [ self._reverse[v] for v in self.values() ]
