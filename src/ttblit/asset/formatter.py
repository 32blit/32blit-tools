import importlib
import pkgutil

from . import formatters


class AssetFormatter():
    _by_name = {}
    _by_extension = {}

    def __init__(self, components=None, extensions=None):
        self.components = components if components else (None, )
        self.extensions = extensions

    def __call__(self, fragment_func):
        """Decorator method to create a formatter instance from a fragment function."""
        self.name = fragment_func.__name__
        self.fragments = fragment_func
        return self

    def joiner(self, join_func):
        """Decorator method to attach a join function to a formatter and register it."""
        self.join = join_func
        # Now we have all we need to register.
        self._by_name[self.name] = self
        for ext in self.extensions:
            self._by_extension[ext] = self
        return self

    def __repr__(self):
        return self.name

    @staticmethod
    def fragments(symbol, data):
        raise NotImplementedError

    @staticmethod
    def join(ext, filename, data):
        raise NotImplementedError

    @classmethod
    def names(cls):
        return cls._by_name.keys()

    @classmethod
    def parse(cls, value):
        """Fetch a formatter by name."""
        if isinstance(value, cls):
            return value
        else:
            try:
                return cls._by_name[value]
            except KeyError:
                raise ValueError(f'Invalid format {value}, choices {cls.names()}.')

    @classmethod
    def guess(cls, path):
        """Fetch a formatter which can generate the requested filename."""
        try:
            return cls._by_extension[path.suffix]
        except KeyError:
            raise TypeError(f"Unable to identify format for {path}.")


# Load all the implementations dynamically.
for loader, module_name, is_pkg in pkgutil.walk_packages(formatters.__path__, formatters.__name__ + '.'):
    # We don't need to import anything from the modules. We just need to load them.
    # This will cause the decorators to run, which registers the formatters.
    importlib.import_module(module_name, formatters.__name__)
