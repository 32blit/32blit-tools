
__version__ = '0.7.1'

import logging

import click

from .asset.builder import AssetTool
from .tool.cmake import cmake_cli
from .tool.dfu import dfu_cli
from .tool.flasher import flash_cli, install_cli, launch_cli
from .tool.metadata import metadata_cli
from .tool.packer import pack_cli
from .tool.relocs import relocs_cli
from .tool.setup import setup_cli


@click.group()
@click.option('--debug', is_flag=True)
@click.option('-v', '--verbose', count=True)
def main(debug, verbose):
    log_format = '%(levelname)s: %(message)s'

    log_verbosity = min(verbose, 3)
    log_level = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG][log_verbosity]
    logging.basicConfig(level=log_level, format=log_format)


for n, c in AssetTool._commands.items():
    main.add_command(c)

main.add_command(cmake_cli)
main.add_command(flash_cli)
main.add_command(install_cli)
main.add_command(launch_cli)
main.add_command(metadata_cli)
main.add_command(pack_cli)
main.add_command(relocs_cli)
main.add_command(setup_cli)
main.add_command(dfu_cli)


@main.command(help='Print version and exit')
def version():
    print(__version__)
