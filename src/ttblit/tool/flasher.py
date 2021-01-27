import functools
import logging
import pathlib
import textwrap

import click

from ..core.blitserial import BlitSerial

block_size = 64 * 1024


@click.group('flash', help='Flash a binary or save games/files to 32Blit')
def flash_cli():
    pass


def serial_command(fn):
    """Set up and tear down serial connections."""

    @click.option('ports', '--port', multiple=True, help='Serial port')
    @functools.wraps(fn)
    def _decorated(ports, **kwargs):
        if not ports:
            ports = BlitSerial.find_comport()

        for port in ports:
            with BlitSerial(port) as sp:
                fn(sp, **kwargs)

    return _decorated


@flash_cli.command()
@serial_command
@click.option('--file', type=pathlib.Path, required=True, help='File to save')
@click.option('--directory', type=str, default='/', help='Target directory')
def save(blitserial, file, directory):
    blitserial.reset_to_firmware()
    blitserial.send_file(file, 'sd', directory=directory)


@flash_cli.command()
@serial_command
@click.option('--file', type=pathlib.Path, required=True, help='File to save')
def flash(blitserial, file):
    blitserial.reset_to_firmware()
    blitserial.send_file(file, 'flash')


# TODO: options should be mutually exclusive
@flash_cli.command()
@serial_command
@click.option('--offset', type=int, help='Flash offset of game to delete')
@click.option('--block', type=int, help='Flash block of game to delete')
def delete(blitserial, offset, block):
    blitserial.reset_to_firmware()
    if offset is None:
        offset = block * block_size
    blitserial.erase(offset)


@flash_cli.command()
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


@flash_cli.command()
@serial_command
def debug(blitserial):
    pass


@flash_cli.command()
@serial_command
def reset(blitserial):
    logging.info('Resetting your 32Blit...')
    blitserial.reset()


@flash_cli.command()
@serial_command
def info(blitserial):
    logging.info('Getting 32Blit run status...')
    print(f'Running: {blitserial.status}')
