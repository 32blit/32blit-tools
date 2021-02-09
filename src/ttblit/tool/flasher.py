import functools
import logging
import pathlib
import textwrap

import click

from ..core.blitserial import BlitSerial

block_size = 64 * 1024


@click.group('flash', help='Flash a binary or save games/files to 32Blit')
@click.option('ports', '--port', multiple=True, help='Serial port')
@click.pass_context
def flash_cli(ctx, ports):
    print(ports)
    ctx.obj = ports


def serial_command(fn):
    """Set up and tear down serial connections."""

    @click.option('ports', '--port', multiple=True, help='Serial port')
    @click.pass_context
    @functools.wraps(fn)
    def _decorated(ctx, ports, **kwargs):
        if ctx.obj:
            ports = ctx.obj + ports
        if not ports or ports[0].lower() == 'auto':
            ports = BlitSerial.find_comport()

        for port in ports:
            with BlitSerial(port) as sp:
                fn(sp, **kwargs)

    return _decorated


@flash_cli.command(help="Deprecated: use '32blit install' instead. Copy a file to SD card")
@serial_command
@click.option('--file', type=pathlib.Path, required=True, help='File to save')
@click.option('--directory', type=str, default='/', help='Target directory')
def save(blitserial, file, directory):
    blitserial.reset_to_firmware()
    blitserial.send_file(file, 'sd', directory=directory)


@flash_cli.command(help="Deprecated: use '32blit install' instead. Install a .blit to flash")
@serial_command
@click.option('--file', type=pathlib.Path, required=True, help='File to save')
def flash(blitserial, file):
    blitserial.reset_to_firmware()
    blitserial.send_file(file, 'flash')


# TODO: options should be mutually exclusive
@flash_cli.command(help="Delete a .blit from flash by block index or offset")
@serial_command
@click.option('--offset', type=int, help='Flash offset of game to delete')
@click.option('--block', type=int, help='Flash block of game to delete')
def delete(blitserial, offset, block):
    blitserial.reset_to_firmware()
    if offset is None:
        offset = block * block_size
    blitserial.erase(offset)


@flash_cli.command(help="List .blits installed in flash memory")
@serial_command
def list(blitserial):
    blitserial.reset_to_firmware()
    for meta, offset, size in blitserial.list():
        offset_blocks = offset // block_size
        size_blocks = (size - 1) // block_size + 1

        print(f"Game at block {offset_blocks}")
        print(f"Size: {size_blocks:3d} blocks ({size / 1024:.1f}kB)")

        if meta is not None:
            print(textwrap.dedent(f"""\
                Title:       {meta.data.title}
                Description: {meta.data.description}
                Version:     {meta.data.version}
                Author:      {meta.data.author}
            """))


@flash_cli.command(help="Not implemented")
@serial_command
def debug(blitserial):
    pass


@flash_cli.command(help="Reset 32Blit")
@serial_command
def reset(blitserial):
    logging.info('Resetting your 32Blit...')
    blitserial.reset()


@flash_cli.command(help="Get current runtime status of 32Blit")
@serial_command
def info(blitserial):
    logging.info('Getting 32Blit run status...')
    print(f'Running: {blitserial.status}')


@click.command('install', help="Install files to 32Blit")
@serial_command
@click.argument("source", type=pathlib.Path, required=True)
@click.argument("destination", type=pathlib.PurePosixPath, default=None, required=False)
def install_cli(blitserial, source, destination):
    if destination is None and source.suffix.lower() == '.blit':
        drive = 'flash'
    else:
        drive = 'sd'
        if destination is None:
            destination = pathlib.PurePosixPath('/')
        elif not destination.is_absolute():
            destination = pathlib.PurePosixPath('/') / destination

    blitserial.send_file(source, drive, destination)
