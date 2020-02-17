from ttblit.core import AssetBuilder

class Raw(AssetBuilder):
    command = 'raw'
    help = 'Convert raw/binary data for 32Blit'
    types = ['binary', 'csv']
    typemap = {
        'binary': ('.bin', '.raw'),
        'csv': ('.csv')
    }

    def run(self, args):
        AssetBuilder.run(self, args)
        self._guess_type(args)

        extra_args = {
            'variable': args.var
        }

        if args.type == 'csv':
            extra_args['base'] = 10

        output_data = self.build(args.input, args.type, args.format, extra_args)

        self.output(output_data, args.output, args.format, args.force)

    def csv_to_data(self, input_data, base=10):
        try:
            input_data = input_data.decode('utf-8')
        except AttributeError:
            pass

        input_data = input_data.strip()

        # Replace '1, 2, 3' to '1,2,3', might as well do it here
        input_data = input_data.replace(' ', '')

        # Split out into rows on linebreak
        input_data = input_data.split('\n')

        # Split every row into columns on the comma
        input_data = [row.split(',') for row in input_data]

        # Flatten our rows/cols 2d array into a 1d array of bytes
        # Might as well do the int conversion here, to save another loop
        input_data = [int(col, base) for row in input_data for col in row if col != '']

        return input_data

    def csv_to_c_header(self, input_data, variable=None, base=10):
        input_data = self.csv_to_data(input_data, base)
        return self.binary_to_c_header(input_data, variable)

    def csv_to_c_source_hpp(self, input_data, variable=None, base=10):
        input_data = self.csv_to_data(input_data, base)
        return self.binary_to_c_source_hpp(input_data, variable)

    def csv_to_c_source_cpp(self, input_data, variable=None, base=10):
        input_data = self.csv_to_data(input_data, base)
        return self.binary_to_c_source_cpp(input_data, variable)