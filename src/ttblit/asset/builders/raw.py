from ..builder import AssetBuilder


class RawAsset(AssetBuilder):
    command = 'raw'
    help = 'Convert raw/binary or csv data for 32Blit'
    typemap = {
        'binary': {
            '.bin': True,
            '.raw': True,
        },
        'csv': {
            '.csv': True
        }
    }

    def csv_to_list(self, input_data, base):
        if type(input_data) == bytes:
            input_data = input_data.decode('utf-8')

        # Strip leading/trailing whitespace
        input_data = input_data.strip()

        # Replace '1, 2, 3' to '1,2,3', might as well do it here
        input_data = input_data.replace(' ', '')

        # Split out into rows on linebreak
        input_data = input_data.split('\n')

        # Split every row into columns on the comma
        input_data = [row.split(',') for row in input_data]

        # Flatten our rows/cols 2d array into a 1d array of bytes
        # Might as well do the int conversion here, to save another loop
        return [int(col, base) for row in input_data for col in row if col != '']

    def csv_to_binary(self, input_data, base):
        return bytes(self.csv_to_list(input_data, base))

    def to_binary(self, input_data):
        if self.input_type == 'csv':
            input_data = bytes(self.csv_to_list(input_data, base=10))
        return input_data
