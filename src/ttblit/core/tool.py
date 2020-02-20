class Tool():
    options = {}

    def __init__(self, parser):
        self.parser = parser.add_parser(self.command, help=self.help)

    def run(self, args):
        raise NotImplementedError

    def output(self, output_data, output_file, output_format, force=False):
        if output_file is None:
            output_data = output_format().join(None, output_file, output_data)
            print(output_data)
        else:
            if type(output_data) is dict:
                for extension, data in output_data.items():
                    data = output_format().join(extension, output_file, data)
                    self.write_file(output_file.with_suffix(f'.{extension}'), data, force)
            else:
                output_data = output_format().join(None, output_file, output_data)
                self.write_file(output_file, output_data, force)

    def write_file(self, output_file, output_data, force=False):
        if output_file.exists() and not force:
            raise ValueError(f'Refusing to overwrite {output_file} (use force)')
        else:
            print(f'Writing {output_file}')
            if type(output_data) is str:
                open(output_file, 'wb').write(output_data.encode('utf-8'))
            else:
                open(output_file, 'wb').write(output_data)
