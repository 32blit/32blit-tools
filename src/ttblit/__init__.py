
__version__ = '0.3.0'

import argparse
import logging
import pathlib
import sys

from .asset import font, image, map, raw
from .tool import cmake, flasher, metadata, packer, relocs, version


def exception_handler(exception_type, exception, traceback):
    sys.stderr.write(f"{type(exception).__name__}: {exception}\n")
    sys.stderr.flush()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--debug', action='store_true', help='Enable exception traces')
    parser.add_argument('-v', '--verbosity', action='count', default=0, help='Output verbosity')
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    if len(sys.argv) == 2:
        path = pathlib.Path(sys.argv[1])
        if path.suffix == '.blit':
            sys.argv[1:] = ['flash', 'flash', '--file', str(path)]

    if len(sys.argv) == 3:
        path = pathlib.Path(sys.argv[2])
        if sys.argv[1] == 'flash' and path.suffix == '.blit':
            sys.argv[1:] = ['flash', 'flash', '--file', str(path)]

    tools = {}

    tools[image.ImageAsset.command] = image.ImageAsset(subparsers)
    tools[font.FontAsset.command] = font.FontAsset(subparsers)
    tools[map.MapAsset.command] = map.MapAsset(subparsers)
    tools[raw.RawAsset.command] = raw.RawAsset(subparsers)

    # Add the non-asset tools
    tools[packer.Packer.command] = packer.Packer(subparsers)
    tools[cmake.CMake.command] = cmake.CMake(subparsers)
    tools[flasher.Flasher.command] = flasher.Flasher(subparsers)
    tools[metadata.Metadata.command] = metadata.Metadata(subparsers)
    tools[relocs.Relocs.command] = relocs.Relocs(subparsers)
    tools[version.Version.command] = version.Version(subparsers)

    args = parser.parse_args()

    log_format = '%(levelname)s: %(message)s'

    log_verbosity = min(args.verbosity, 3)
    log_level = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG][log_verbosity]
    logging.basicConfig(level=log_level, format=log_format)

    if args.debug:
        logging.basicConfig(level=logging.DEBUG, format=log_format)
    else:
        sys.excepthook = exception_handler

    if args.command is None:
        parser.print_help()
    else:
        sys.exit(tools[args.command].run(args))
