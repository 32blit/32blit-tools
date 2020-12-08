import pytest


def test_version(parsers, capsys):
    from ttblit.tool import version
    from ttblit import __version__

    parser, subparser = parsers

    version = version.Version(subparser)

    args = parser.parse_args([
        'version'])

    version.run(args)

    assert capsys.readouterr().out == f'{__version__}\n'
