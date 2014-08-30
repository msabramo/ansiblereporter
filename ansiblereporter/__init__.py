
from systematic.log import Logger

__version__ = '1.0'

class SortedDict(dict):
    compare_fields = ()

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        self.log = Logger().default_stream

    def __cmp__(self, other):
        if self.compare_fields:
            for key in self.compare_fields:
                a = getattr(key, self)
                b = getattr(key, other)
                if a != b:
                    return cmp(a, b)

            return 0

        else:
            cmp(self, other)

    def __iter__(self):
        return self

    def next(self):
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
        return [k for k in sorted(dict.keys(self))]

    def items(self):
        return [(k, self[k]) for k in self.keys()]

    def values(self):
        return [self[k] for k in self.keys()]

    def copy(self):
        return SortedDict((k,v) for k,v in self.items())

