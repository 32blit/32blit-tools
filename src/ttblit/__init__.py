
__version__ = '0.0.1'

import argparse

from .asset import builder, image, map, raw, sprite


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    tools = {}

    tools[builder.Builder.command] = builder.Builder(subparsers)
    tools[image.Builder.command] = image.Builder(subparsers)
    tools[map.Builder.command] = map.Builder(subparsers)
    tools[raw.Builder.command] = raw.Builder(subparsers)
    tools[sprite.Builder.command] = sprite.Builder(subparsers)

    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
    else:
        tools[args.command].run(args)