import logging

from .formatter import AssetFormatter


class AssetWriter:

    def __init__(self):
        self._assets = {}

    def add_asset(self, symbol, data):
        if symbol in self._assets:
            raise NameError(f'Symbol {symbol} has already been added.')
        self._assets[symbol] = data

    def _sorted(self, sort):
        if sort is None:
            return self._assets.items()
        elif sort == 'symbol':
            return sorted(self._assets.items())
        elif sort == 'size':
            return sorted(self._assets.items(), key=lambda i: len(i[1]))
        else:
            raise ValueError(f"Don't know how to sort by {sort}.")

    def _get_format(self, value, path, default='c_header'):
        if value is None:
            if path is None:
                logging.warning(f"No output filename, writing to stdout assuming {default}")
                return AssetFormatter.parse(default)
            else:
                fmt = AssetFormatter.guess(path)
                logging.info(f"Guessed output format {fmt} for {path}")
                return fmt
        else:
            return AssetFormatter.parse(value)

    def write(self, fmt=None, path=None, force=False, report=True, sort=None):
        fmt = self._get_format(fmt, path)
        assets = self._sorted(sort)
        fragments = [fmt.fragments(symbol, data) for symbol, data in assets]
        components = {key: [f[key] for f in fragments] for key in fragments[0]}
        outpaths = []

        for component, data in fmt.join(path, components).items():
            if path is None:
                print(data)
            else:
                outpath = path if component is None else path.with_suffix(f'.{component}')
                if outpath.exists() and not force:
                    raise FileExistsError(f'Refusing to overwrite {path} (use force)')
                else:
                    logging.info(f'Writing {outpath}')
                    if type(data) is str:
                        outpath.write_text(data, encoding='utf8')
                    else:
                        outpath.write_bytes(data)
                outpaths.append(outpath)

        if path and report:
            lines = [
                f'Formatter: {fmt.name}',
                'Files:', *(f'    {path}' for path in outpaths),
                'Assets:', *('    {}: {}'.format(symbol, len(data)) for symbol, data in assets),
                'Total size: {}'.format(sum(len(data) for symbol, data in assets)),
                '',
            ]
            path.with_name(path.stem + '_report.txt').write_text('\n'.join(lines))
