
__version__ = '0.6.0'

import click

from .asset.builder import AssetTool
from .tool.cmake import cmake_cli
from .tool.flasher import flash_cli, install_cli
from .tool.metadata import metadata_cli
from .tool.packer import pack_cli
from .tool.relocs import relocs_cli


@click.group()
@click.option('--debug', is_flag=True)
def main(debug):
    pass


for n, c in AssetTool._commands.items():
    main.add_command(c)

main.add_command(cmake_cli)
main.add_command(flash_cli)
main.add_command(install_cli)
main.add_command(metadata_cli)
main.add_command(pack_cli)
main.add_command(relocs_cli)


@main.command(help='Print version and exit')
def version():
    print(__version__)
