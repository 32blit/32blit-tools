
__version__ = '0.0.1'

import argparse

from .asset import image, map, raw, sprite
from .tool import packer


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    tools = {}

    tools[sprite.Sprite.command] = sprite.Sprite(subparsers)
    tools[map.Map.command] = map.Map(subparsers)
    tools[raw.Raw.command] = raw.Raw(subparsers)
    tools[image.Image.command] = image.Image(subparsers)

    _packer = packer.Packer(subparsers)

    # Register the asset tools with the packer
    _packer.register_asset_builders(tools)

    # Add the non-asset tools
    tools[packer.Packer.command] = _packer

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    else:
        tools[args.command].run(args)