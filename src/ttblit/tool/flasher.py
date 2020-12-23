import functools
import logging
import pathlib
import textwrap

from ..core.tool import Tool
from ..core.blitserial import BlitSerial


def serial_command(fn):
    """Set up and tear down serial connections."""

    @functools.wraps(fn)
    def _decorated(self, args):
        ports = args.get('port', None)
        if ports is None:
            ports = BlitSerial.find_comport()

        for port in ports:
            with BlitSerial(port) as sp:
                fn(self, sp, args)

    return _decorated


class Flasher(Tool):
    command = 'flash'
    help = 'Flash a binary or save games/files to 32Blit'

    block_size = 64 * 1024

    def __init__(self, subparser):
        Tool.__init__(self, subparser)

        self.parser.add_argument('--port', help='Serial port')

        operations = self.parser.add_subparsers(dest='operation', help='Flasher operations')

        self.op_save = operations.add_parser('save', help='Save a game/file to your 32Blit')
        self.op_save.add_argument('--file', type=pathlib.Path, required=True, help='File to save')
        self.op_save.add_argument('--directory', type=str, default='/', help='Target directory')

        self.op_flash = operations.add_parser('flash', help='Flash a game to your 32Blit')
        self.op_flash.add_argument('--file', type=pathlib.Path, required=True, help='File to flash')

        self.op_delete = operations.add_parser('delete', help='Delete a game/file from your 32Blit')
        group = self.op_delete.add_mutually_exclusive_group(required=True)
        group.add_argument('--offset', type=int, help='Flash offset of game to delete')
        group.add_argument('--block', type=int, help='Flash block of game to delete')

        self.op_list = operations.add_parser('list', help='List games/files on your 32Blit')
        self.op_debug = operations.add_parser('debug', help='Enter serial debug mode')
        self.op_reset = operations.add_parser('reset', help='Reset your 32Blit')
        self.op_info = operations.add_parser('info', help='Get 32Blit run status')

    def run(self, args):
        if args.operation is not None:
            dispatch = f'run_{args.operation}'
            getattr(self, dispatch)(vars(args))

    @serial_command
    def run_save(self, blitserial, args):
        blitserial.reset_to_firmware()
        blitserial.send_file(args.get('file'), 'sd', directory=args.get('directory'))

    @serial_command
    def run_flash(self, blitserial, args):
        blitserial.reset_to_firmware()
        blitserial.send_file(args.get('file'), 'flash')

    @serial_command
    def run_delete(self, blitserial, args):
        blitserial.reset_to_firmware()
        offset = args.get('offset')
        if offset is None:
            offset = args.get('block') * self.block_size
        blitserial.erase(offset)

    @serial_command
    def run_list(self, blitserial, args):
        blitserial.reset_to_firmware()
        for meta, offset, size in blitserial.list():
            offset_blocks = offset // self.block_size
            size_blocks = (size - 1) // self.block_size + 1

            print(f"Game at block {offset_blocks}")
            print(f"Size: {size_blocks:3d} blocks ({size / 1024:.1f}kB)")

            if meta is not None:
                print(textwrap.dedent(f"""\
                    Title:       {meta.data.title}
                    Description: {meta.data.description}
                    Version:     {meta.data.version}
                    Author:      {meta.data.author}
                """))

    @serial_command
    def run_debug(self, blitserial, args):
        pass

    @serial_command
    def run_reset(self, blitserial, args):
        logging.info('Resetting your 32Blit...')
        blitserial.reset()

    @serial_command
    def run_info(self, blitserial, args):
        logging.info('Getting 32Blit run status...')
        print(f'Running: {blitserial.status}')
