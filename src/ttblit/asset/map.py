from ttblit.core import AssetBuilder
from ttblit.asset.raw import Raw

class Map(Raw):
    command = 'map'
    help = 'Convert popular tilemap formats for 32Blit'
    types = ['tiled']
    typemap = {
        'tiled': ('.tmx', '.raw'),
    }

    def tiled_to_binary(self, input_data):
        from xml.etree import ElementTree as ET
        root = ET.fromstring(input_data)
        layers = root.findall('layer/data')
        data = []
        for layer in layers:
            data += self.csv_to_data(
                    layer.text,
                    base=10)
        return data

    def tiled_to_c_source_cpp(self, input_data, variable=None):
        return self.tiled_to_c_header(input_data, variable=variable)

    def tiled_to_c_source_hpp(self, input_data, variable=None):
        return self.binary_to_c_source_hpp(input_data, variable)

    def tiled_to_c_header(self, input_data, variable=None):
        data = self.tiled_to_binary(input_data)
        return self.binary_to_c_header(data, variable)