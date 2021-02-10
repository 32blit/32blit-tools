import logging
import pathlib

import click

from ..asset.builder import AssetBuilder, make_symbol_name
from ..asset.writer import AssetWriter
from ..core.yamlloader import YamlLoader


class Packer(YamlLoader):

    def run(self, config, output, files, force):
        if config is None and not files:
            raise click.UsageError('You must supply a config or list of input files.')
        self.targets = []
        self.setup_for_config(config, output, files)

        # Top level of our config is filegroups and general settings
        for target, options in self.config.items():
            output_file = self.working_path / target
            logging.info(f'Preparing output target {output_file}')

            asset_sources = []
            target_options = {}

            for key, value in options.items():
                if key in ('prefix', 'type'):
                    target_options[key] = value

            # Strip high-level options from the dict
            # Leaving just file source globs
            for key in target_options:
                options.pop(key)

            for file_glob, file_options in options.items():
                # Treat the input string as a glob, and get an input filelist
                if type(file_glob) is str:
                    input_files = list(self.working_path.glob(file_glob))
                else:
                    input_files = [file_glob]
                if len(input_files) == 0:
                    logging.warning(f'Input file(s) not found {self.working_path / file_glob}')
                    continue

                # Rewrite a single string option to `name: option`
                # This handles: `inputfile.bin: filename` entries
                if type(file_options) is str:
                    file_options = {'name': file_options}

                elif file_options is None:
                    file_options = {}

                # Handle both an array of options dicts or a single dict
                if type(file_options) is not list:
                    file_options = [file_options]

                for file_opts in file_options:
                    asset_sources.append((input_files, file_opts))

            self.targets.append((
                output_file,
                asset_sources,
                target_options
            ))

        self.destination_path.mkdir(parents=True, exist_ok=True)

        for path, sources, options in self.targets:
            aw = AssetWriter()
            for input_files, file_opts in sources:
                for asset in self.build_assets(input_files, self.working_path, prefix=options.get('prefix'), **file_opts):
                    aw.add_asset(*asset)

            aw.write(options.get('type'), self.destination_path / path.name, force=force)

    def build_assets(self, input_files, working_path, name=None, type=None, prefix=None, **builder_options):
        if type is None:
            # Glob files all have the same suffix, so we only care about the first one
            try:
                typestr = AssetBuilder.guess_builder(input_files[0])
            except TypeError:
                logging.warning(f'Unable to guess type, assuming raw/binary {input_files[0]}.')
                typestr = 'raw/binary'
        else:
            typestr = type

        input_type, input_subtype = typestr.split('/')
        builder = AssetBuilder._by_name[input_type]

        # Now we know our target builder, one last iteration through the options
        # allows some pre-processing stages to remap paths or other idiosyncrasies
        # of the yml config format.
        # Currently the only option we need to do this on is 'palette' for images.
        for option in ['palette']:
            try:
                if not pathlib.Path(builder_options[option]).is_absolute():
                    builder_options[option] = working_path / builder_options[option]
            except KeyError:
                pass

        for file in input_files:
            symbol_name = make_symbol_name(
                base=name, working_path=working_path, input_file=file,
                input_type=input_type, input_subtype=input_subtype, prefix=prefix
            )

            yield symbol_name, builder.from_file(file, input_subtype, **builder_options)
            logging.info(f' - {typestr} {file} -> {symbol_name}')


@click.command('pack', help='Pack a collection of assets for 32Blit')
@click.option('--config', type=pathlib.Path, help='Asset config file')
@click.option('--output', type=pathlib.Path, help='Name for output file(s) or root path when using --config')
@click.option('--files', multiple=True, type=pathlib.Path, help='Input files')
@click.option('--force', is_flag='store_true', help='Force file overwrite')
def pack_cli(config, output, files, force):
    Packer().run(config, output, files, force)
