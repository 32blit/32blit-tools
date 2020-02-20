from ttblit.asset.raw import RawAsset


class MapAsset(RawAsset):
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
                base=10,
                offset=-1)  # Tiled indexes from 1 rather than 0
        return data

    def tiled_to_c_source_cpp(self, input_data):
        return self.tiled_to_c_header(input_data)

    def tiled_to_c_source_hpp(self, input_data):
        return self.binary_to_c_source_hpp(input_data)

    def tiled_to_c_header(self, input_data):
        data = self.tiled_to_binary(input_data)
        return self.binary_to_c_header(data)
