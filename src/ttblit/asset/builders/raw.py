from ..builder import AssetBuilder, AssetTool

binary_typemap = {
    'binary': {
        '.bin': True,
        '.raw': True,
    },
    'csv': {
        '.csv': True
    }
}


def csv_to_list(input_data, base):
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


@AssetBuilder(typemap=binary_typemap)
def raw(data, subtype):
    if subtype == 'csv':
        return bytes(csv_to_list(data, base=10))
    else:
        return data


@AssetTool(raw, 'Convert raw/binary or csv data for 32Blit')
def raw_cli(input_file, input_type):
    return raw.from_file(input_file, input_type)
