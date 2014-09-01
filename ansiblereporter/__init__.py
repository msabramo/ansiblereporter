"""
Ansible output report parser hooks
"""

from systematic.log import Logger

__version__ = '1.0'


class RunnerError(Exception): pass


class SortedDict(dict):
    """Sorted dictionary

    Implementation of a sorted dictionary, sorted by list of key names in
    self.compare_fields set.
    """
    compare_fields = ()

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.log = Logger().default_stream

    def __cmp__(self, other):
        """Compare with self.compare_fields

        Compare with keys in self.compare_fields, or by plain cmp(self, other)
        if no compare_fields keys were set.
        """
        if self.compare_fields:
            for key in self.compare_fields:
                a = getattr(self, key)
                b = getattr(other, key)
                if a != b:
                    return cmp(a, b)
            return 0

        else:
            cmp(self, other)

    def __iter__(self):
        """Iterate sorted keys

        Iterator for sorted dictionary keys
        """
        return self

    def next(self):
        """Iterator for sorted keys

        Standard iterator to iterate over sorted dictionary keys
        """
        if not hasattr(self, '__iter_index__') or self.__iter_index__ is None:
            self.__iter_index__ = 0
            self.__iter_keys__ = self.keys()

        try:
            entry = self.__iter_keys__[self.__iter_index__]
            self.__iter_index__ += 1
            return entry

        except KeyError:
            self__iter__index__ = None
            self.__iter__keys = None

        except IndexError:
            self__iter__index__ = None
            self.__iter__keys = None
            raise StopIteration

    def keys(self):
        """Return keys as sorted list"""
        return [k for k in sorted(dict.keys(self))]

    def items(self):
        """Return items sorted by self.keys()"""
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        """Return values sorted by self.keys()"""
        return [self[k] for k in self.keys()]

    def copy(self):
        """Return a new SortedDict copy"""
        return SortedDict((k,v) for k,v in self.items())

