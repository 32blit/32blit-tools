
__version__ = '0.0.5'

import argparse
import pathlib
import sys

from .asset import image, map, raw
from .tool import cmake, flasher, packer


def exception_handler(exception_type, exception, traceback):
    print(f"{type(exception).__name__}: {exception}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    if len(sys.argv) == 2:
        file = pathlib.Path(sys.argv[1])
        if file.is_file() and file.exists():
            f = flasher.Flasher(subparsers)
            f.run_save({'file': file})
            return

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
    tools[flasher.Flasher.command] = flasher.Flasher(subparsers)

    args = parser.parse_args()

    if not args.debug:
        sys.excepthook = exception_handler

    if args.command is None:
        parser.print_help()
    else:
        tools[args.command].run(args)
