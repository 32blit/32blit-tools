import pkgutil

from . import formatters


class OutputFormat():
    name = 'none'
    components = None
    extensions = ()

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def build(self, input_data, symbol_name):
        if self.components is None:
            return self.output(input_data, symbol_name)
        else:
            output_components = {}
            for extension in self.components:
                output_components[extension] = getattr(self, f'output_{extension}')(input_data, symbol_name)
            return output_components


output_formats = {}


def parse_output_format(value):
    if type(value) is str:
        return output_formats.get(value, None)
    if issubclass(value, OutputFormat):
        return value
    return output_formats[value]


# Load all the implementations dynamically.
for loader, module_name, is_pkg in pkgutil.walk_packages(formatters.__path__, formatters.__name__ + '.'):
    module = loader.find_module(module_name).load_module(module_name)
    # Import the implementations to this module, so others can access them.
    # TODO: Refactor the registration system so we don't need to do this.
    for name, obj in module.__dict__.items():
        try:
            if issubclass(obj, OutputFormat):
                output_formats[obj.name] = obj
                globals()[name] = obj
        except TypeError:
            pass
