import struct

from .raw import RawAsset


class MapAsset(RawAsset):
    command = 'map'
    help = 'Convert popular tilemap formats for 32Blit'
    typemap = {
        'tiled': {
            '.tmx': True,
            '.raw': False,
        },
    }

    def __init__(self, parser=None):
        self.options.update({
            'empty_tile': (int, 0),
            'output_struct': (bool, False)
        })

        RawAsset.__init__(self, parser)

        self.empty_tile = 0
        self.output_struct = False

        if self.parser is not None:
            self.parser.add_argument('--empty-tile', type=int, default=0, help='Remap .tmx empty tiles')
            self.parser.add_argument('--output-struct', type=bool, default=False, help='Output .tmx as struct with level width/height, etc')

    def tiled_to_binary(self, input_data):
        from xml.etree import ElementTree as ET
        root = ET.fromstring(input_data)
        layers = root.findall('layer')
        map_data = root.find('map')
        layer_data = []
        # Sort layers by ID (since .tmx files can have them in arbitrary orders)
        layers.sort(key=lambda l: int(l.get('id')))
        for layer_csv in layers:
            layer = self.csv_to_list(layer_csv.find('data').text, 10)
            # Shift 1-indexed tiles to 0-indexed, and remap empty tile (0) to specified index
            layer = [self.empty_tile if i == 0 else i - 1 for i in layer]
            layer_data.append(bytes(layer))

        if self.output_struct:  # Fancy struct
            width = int(root.get("width"))
            height = int(root.get("height"))
            layers = len(layer_data)

            map_data = bytes('MTMX', encoding='utf-8')
            map_data += struct.pack('<BHHH', self.empty_tile, width, height, layers)
            map_data += b''.join(layer_data)

            return map_data

        else:  # Just return the raw layer data (legacy compatibility mode)
            return b''.join(layer_data)

    def to_binary(self, input_data):
        if self.input_type == 'tiled':
            return self.tiled_to_binary(input_data)
