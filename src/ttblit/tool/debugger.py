import functools
import logging
import pathlib
import textwrap

import click

from ..core.blitserial import BlitSerial

block_size = 64 * 1024


@click.group('debug', help='Read/write debug messages to the 32blit')
@click.option('ports', '--port', multiple=True, help='Serial port')
@click.pass_context
def debug_cli(ctx, ports):
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


@debug_cli.command(help="Send a 32BLUSER message")
@serial_command
@click.argument('message', type=str, required=True)
def message(blitserial, message):
    blitserial.user(message)
    print(f"Writing user message \"{message}\"")


@debug_cli.command(help="Read serial output from 32blit")
@serial_command
def read(blitserial):
    for line in blitserial.readlines():
        print(line)
