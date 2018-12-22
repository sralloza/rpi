# -*- coding: utf-8 -*-


class DinamicAttributes:
    """Class with dynamically modifiable properties."""

    def __init__(self, **kwargs):
        _dict = kwargs.pop('dict', None)
        if _dict is not None:
            for key, value in _dict.items():
                self[key] = value

        for key, value in kwargs.items():
            self[key] = value

    def __getitem__(self, name):
        return getattr(self, name)

    def __setitem__(self, name, value):
        return setattr(self, name, value)

    def __delitem__(self, name):
        return delattr(self, name)

    def __contains__(self, name):
        return hasattr(self, name)

    @property
    def dict(self):
        return self.__dict__

    def __str__(self):
        return str(self.dict)

    def __repr__(self):
        foo = 'DinamicAttributes('
        keys, values = self.dict.keys(), self.dict.values()
        joined = [[x, y] for x, y in zip(keys, values)]
        pairs = [f"{k[0]}={k[1]}" if type(k[1]) != str else f"{k[0]}='{k[1]}'" for k in joined]
        foo += ", ".join(pairs)
        return foo + ')'
