class Tool():
    options = {}

    def __init__(self, parser=None):
        self.parser = None
        if parser is not None:
            self.parser = parser.add_parser(self.command, help=self.help)

    def run(self, args):
        raise NotImplementedError
