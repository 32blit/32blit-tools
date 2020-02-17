from ttblit.core import AssetBuilder
from ttblit.asset.raw import Raw

class Map(Raw):
    command = 'map'
    help = 'Convert popular tilemap formats for 32Blit'
    types = ['tiled']
    typemap = {
        'tiled': ('.tmx', '.raw'),
    }

    def tiled_to_c_header(self, input_data, variable=None):
        from xml.etree import ElementTree as ET
        root = ET.fromstring(input_data)
        layers = root.findall('layer/data')
        data = []
        for layer in layers:
            data.append(
                self.csv_to_c_header(
                    layer.text,
                    variable,
                    base=10
                )
            )

        return '\n'.join(data)