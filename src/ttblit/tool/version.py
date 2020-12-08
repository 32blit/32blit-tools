from ttblit import __version__

from ..core.tool import Tool


class Version(Tool):
    command = 'version'
    help = 'Print the current 32blit version'

    def run(self, args):
        print(__version__)
