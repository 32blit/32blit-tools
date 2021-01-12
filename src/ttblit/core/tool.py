import logging
import pathlib

import yaml


class Tool():
    options = {}

    def __init__(self, parser=None):
        self.parser = None
        if parser is not None:
            self.parser = parser.add_parser(self.command, help=self.help)

    def setup_for_config(self, config_file, output_path, files=None):
        self.working_path = pathlib.Path('.')
        if config_file is not None:
            if config_file.is_file():
                self.working_path = config_file.parent
            else:
                logging.warning(f'Unable to find config at {config_file}')
            self.config = yaml.safe_load(config_file.read_text())
            logging.info(f'Using config at {config_file}')

        elif files is not None and output_path is not None:
            self.config = {output_path: {file: {} for file in files}}

        if output_path is not None:
            self.destination_path = output_path
        else:
            self.destination_path = self.working_path

    def run(self, args):
        raise NotImplementedError
