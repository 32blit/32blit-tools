import pathlib

import click

from ..core import dfu


@click.group('dfu', help='Pack or unpack DFU files')
def dfu_cli():
    pass


@dfu_cli.command(help='Pack a .bin file into a DFU file')
@click.option('--input-file', type=pathlib.Path, help='Input .bin', required=True)
@click.option('--output-file', type=pathlib.Path, help='Output .dfu', required=True)
@click.option('--address', type=int, help='Offset address', default=0x08000000)
@click.option('--force/--no-force', help='Force file overwrite', default=True)
def build(input_file, output_file, address, force):
    dfu.build(input_file, output_file, address, force)


@dfu_cli.command(help='Dump the .bin parts of a DFU file')
@click.option('--input-file', type=pathlib.Path, help='Input .bin', required=True)
@click.option('--force/--no-force', help='Force file overwrite', default=True)
def dump(input_file, force):
    dfu.dump(input_file, force)


@dfu_cli.command(help='Read information from a DFU file')
@click.option('--input-file', type=pathlib.Path, help='Input .bin', required=True)
def read(input_file):
    parsed = dfu.read(input_file)
    dfu.display_dfu_info(parsed)
