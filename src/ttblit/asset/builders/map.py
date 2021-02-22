import struct
import logging

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
    layer_data = []
    # Sort layers by ID (since .tmx files can have them in arbitrary orders)
    layers.sort(key=lambda l: int(l.get('id')))

    use_16bits = False

    for layer_csv in layers:
        layer = csv_to_list(layer_csv.find('data').text, 10)
        # Shift 1-indexed tiles to 0-indexed, and remap empty tile (0) to specified index
        layer = [empty_tile if i == 0 else i - 1 for i in layer]

        if max(layer) > 255 and not use_16bits:
            # Let's assume it's got 2-byte tile indices
            logging.info('Found a tile index > 255, using 16bit tile sizes!')
            use_16bits = True

        # Always build up a 1d array of layer data
        layer_data += layer

    if use_16bits:
        layer_data = struct.pack(f'<{len(layer_data)}H', *layer_data)
    else:
        layer_data = struct.pack(f'<{len(layer_data)}B', *layer_data)

    if output_struct:  # Fancy struct
        layer_count = len(layers)
        width = int(root.get("width"))
        height = int(root.get("height"))

        return struct.pack(
            '<4sBHHH',
            bytes('MTMX', encoding='utf-8'),
            empty_tile,
            width,
            height,
            layer_count
        ) + layer_data

    else:
        # Just return the raw layer data
        return layer_data


@AssetBuilder(typemap=map_typemap)
def map(data, subtype, empty_tile=0, output_struct=False):
    if subtype == 'tiled':
        return tiled_to_binary(data, empty_tile, output_struct)


@AssetTool(map, 'Convert popular tilemap formats for 32Blit')
@click.option('--empty-tile', type=int, default=0, help='Remap .tmx empty tiles')
@click.option('--output-struct', type=bool, default=False, help='Output .tmx as struct with level width/height, etc')
def map_cli(input_file, input_type, **kwargs):
    return map.from_file(input_file, input_type, **kwargs)
