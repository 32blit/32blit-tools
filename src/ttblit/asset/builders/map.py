import struct

import click

from ..builder import AssetBuilder, AssetTool
from .raw import csv_to_list

map_typemap = {
    'tiled': {
        '.tmx': True,
        '.raw': False,
    },
}


def tiled_to_binary(data, empty_tile, output_struct):
    from xml.etree import ElementTree as ET
    root = ET.fromstring(data)
    layers = root.findall('layer')
    map_data = root.find('map')
    layer_data = []
    # Sort layers by ID (since .tmx files can have them in arbitrary orders)
    layers.sort(key=lambda l: int(l.get('id')))
    for layer_csv in layers:
        layer = csv_to_list(layer_csv.find('data').text, 10)
        # Shift 1-indexed tiles to 0-indexed, and remap empty tile (0) to specified index
        layer = [empty_tile if i == 0 else i - 1 for i in layer]
        layer_data.append(bytes(layer))

    if output_struct:  # Fancy struct
        width = int(root.get("width"))
        height = int(root.get("height"))
        layers = len(layer_data)

        map_data = bytes('MTMX', encoding='utf-8')
        map_data += struct.pack('<BHHH', empty_tile, width, height, layers)
        map_data += b''.join(layer_data)

        return map_data

    else:  # Just return the raw layer data (legacy compatibility mode)
        return b''.join(layer_data)


@AssetBuilder(typemap=map_typemap)
def map(data, subtype, empty_tile=0, output_struct=False):
    if subtype == 'tiled':
        return tiled_to_binary(data, empty_tile, output_struct)


@AssetTool(map, 'Convert popular tilemap formats for 32Blit')
@click.option('--empty-tile', type=int, default=0, help='Remap .tmx empty tiles')
@click.option('--output-struct', type=bool, default=False, help='Output .tmx as struct with level width/height, etc')
def map_cli(input_file, input_type, **kwargs):
    return map.from_file(input_file, input_type, **kwargs)
