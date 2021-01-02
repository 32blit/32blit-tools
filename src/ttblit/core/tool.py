import logging


class Tool():
    options = {}

    def __init__(self, parser=None):
        self.parser = None
        if parser is not None:
            self.parser = parser.add_parser(self.command, help=self.help)

    def prepare(self, opts):
        for option, option_type in self.options.items():
            default_value = None
            if type(option_type) is tuple:
                option_type, default_value = option_type
            setattr(self, option, opts.get(option, default_value))

    def run(self, args):
        raise NotImplementedError

    def output(self, output_data, output_file, output_format, force=False):
        for extension, data in output_format.join(output_file, output_data).items():
            if output_file is None:
                print(data)
            else:
                if extension:
                    self.write_file(output_file.with_suffix(f'.{extension}'), data, force)
                else:
                    self.write_file(output_file, data, force)

    def write_file(self, output_file, output_data, force=False):
        if output_file.exists() and not force:
            raise ValueError(f'Refusing to overwrite {output_file} (use force)')
        else:
            logging.info(f'Writing {output_file}')
            if type(output_data) is str:
                open(output_file, 'wb').write(output_data.encode('utf-8'))
            else:
                open(output_file, 'wb').write(output_data)
