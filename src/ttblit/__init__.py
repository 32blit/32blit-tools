
__version__ = '0.0.1'

import argparse

from .asset import image, map, raw, sprite
from .tool import packer


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    tools = {}

    tools[packer.Packer.command] = packer.Packer(subparsers)

    tools[image.Image.command] = image.Image(subparsers)
    tools[map.Map.command] = map.Map(subparsers)
    tools[raw.Raw.command] = raw.Raw(subparsers)
    tools[sprite.Sprite.command] = sprite.Sprite(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    else:
        tools[args.command].run(args)