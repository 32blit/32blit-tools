from ..core.assetbuilder import AssetBuilder


class RawAsset(AssetBuilder):
    command = 'raw'
    help = 'Convert raw/binary or csv data for 32Blit'
    types = ['binary', 'csv']
    typemap = {
        'binary': ('.bin', '.raw'),
        'csv': ('.csv')
    }

    def prepare(self, args):
        AssetBuilder.prepare(self, args)

    def csv_to_binary(self, input_data, base=10, offset=0):
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
        input_data = [(int(col, base) + offset) for row in input_data for col in row if col != '']

        return bytes(input_data)

    def to_binary(self, input_data):
        if self.input_type == 'csv':
            input_data = self.csv_to_binary(input_data, base=10)
        return input_data
