
__version__ = '0.0.2'

import argparse
import sys

from .asset import image, map, raw
from .tool import cmake, packer


def exception_handler(exception_type, exception, traceback):
    print(f"Error: {exception}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    tools = {}

    tools[image.ImageAsset.command] = image.ImageAsset(subparsers)
    tools[map.MapAsset.command] = map.MapAsset(subparsers)
    tools[raw.RawAsset.command] = raw.RawAsset(subparsers)

    _packer = packer.Packer(subparsers)

    # Register the asset tools with the packer
    _packer.register_asset_builders(tools)

    # Add the non-asset tools
    tools[packer.Packer.command] = _packer
    tools[cmake.CMake.command] = cmake.CMake(subparsers)

    args = parser.parse_args()

    if not args.debug:
        sys.excepthook = exception_handler

    if args.command is None:
        parser.print_help()
    else:
        tools[args.command].run(args)
