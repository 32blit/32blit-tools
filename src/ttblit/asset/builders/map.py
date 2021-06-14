import logging
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
    layer_data = []
    transform_data = []
    # Sort layers by ID (since .tmx files can have them in arbitrary orders)
    layers.sort(key=lambda l: int(l.get('id')))

    use_16bits = False

    for layer_csv in layers:
        raw_layer = csv_to_list(layer_csv.find('data').text, 10)
        # Shift 1-indexed tiles to 0-indexed, and remap empty tile (0) to specified index
        # The highest three bits store the transform
        layer = [empty_tile if i == 0 else (i & 0x1FFFFFFF) - 1 for i in raw_layer]

        # This matches the flags used by the TileMap class, but doesn't match SpriteTransform...
        layer_transforms = [i >> 29 for i in raw_layer]

        if max(layer) > 255 and not use_16bits:
            # Let's assume it's got 2-byte tile indices
            logging.info('Found a tile index > 255, using 16bit tile sizes!')
            use_16bits = True

        # Always build up a 1d array of layer data
        layer_data += layer
        transform_data += layer_transforms

    if use_16bits:
        layer_data = struct.pack(f'<{len(layer_data)}H', *layer_data)
    else:
        layer_data = struct.pack(f'<{len(layer_data)}B', *layer_data)

    if output_struct:  # Fancy struct
        layer_count = len(layers)
        width = int(root.get("width"))
        height = int(root.get("height"))

        flags = 0

        have_transforms = any(v != 0 for v in transform_data)

        if use_16bits:
            flags |= (1 << 0)

        if have_transforms:
            flags |= (1 << 1)
        else:
            transform_data = []

        return struct.pack(
            '<4sHHHHHH',
            bytes('MTMX', encoding='utf-8'),
            16,
            flags,
            empty_tile,
            width,
            height,
            layer_count
        ) + layer_data + bytes(transform_data)

    else:
        # Just return the raw layer data
        return layer_data + bytes(transform_data)


@AssetBuilder(typemap=map_typemap)
def map(data, subtype, empty_tile=0, output_struct=False):
    if subtype == 'tiled':
        return tiled_to_binary(data, empty_tile, output_struct)


@AssetTool(map, 'Convert popular tilemap formats for 32Blit')
@click.option('--empty-tile', type=int, default=0, help='Remap .tmx empty tiles')
@click.option('--output-struct', type=bool, default=False, help='Output .tmx as struct with level width/height, etc')
def map_cli(input_file, input_type, **kwargs):
    return map.from_file(input_file, input_type, **kwargs)
